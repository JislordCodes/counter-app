using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using ExpenseClassifier.Models;
using ExpenseClassifier.Options;
using ExpenseClassifier.Services;
using ExpenseClassifier.Tools;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace ExpenseClassifier.Agents;

/// <summary>
/// Core contract for the intelligent expense classification service.
/// </summary>
public interface IExpenseClassifierAgent
{
    /// <summary>
    /// Classifies a single expense description using a two-stage agentic workflow:
    /// 1. Primary Policy Agent (with tool calling: <see cref="CompanyPolicyTool"/> and <see cref="SpendingLimitTool"/>).
    /// 2. Fallback General Agent (without tools) if the primary stage results in "Other" or an unrecognized policy category.
    /// Incorporates cache-aside caching to avoid redundant LLM invocations.
    /// </summary>
    /// <param name="expenseDescription">The free-form expense claim description.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A structured classification and compliance response.</returns>
    Task<ResponseDto> Classify(string expenseDescription, CancellationToken cancellationToken = default);

    /// <summary>
    /// Classifies a collection of expense line items concurrently with bounded parallelism
    /// and generates aggregate financial metrics and compliance statistics.
    /// </summary>
    /// <param name="request">The batch request containing department, employee info, and line items.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The batch response containing itemized results and aggregate summary analytics.</returns>
    Task<BatchExpenseResponse> ClassifyBatch(BatchExpenseRequest request, CancellationToken cancellationToken = default);
}

/// <summary>
/// Two-stage, multi-tool agentic implementation of <see cref="IExpenseClassifierAgent"/>:
/// a policy-driven primary stage with tool calling, a general fallback stage without tools,
/// cache-aside caching with key normalization, and bounded-concurrency batch processing.
/// </summary>
public class ExpenseClassifierAgent : IExpenseClassifierAgent
{
    private static readonly HashSet<string> KnownCategories = new(StringComparer.OrdinalIgnoreCase)
    {
        "Transportation", "Food", "Accommodation", "Utilities", "Office Supplies", "Software Subscriptions"
    };

    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };

    private static readonly Regex JsonObjectRegex = new(@"\{[\s\S]*\}", RegexOptions.Compiled);

    private const string Stage1SystemInstructions = """
        You are an enterprise expense classification assistant. Use the get_company_policy and
        get_spending_limits tools to review the official category guidelines before answering.

        Classify the user's expense claim into exactly one of these categories:
        Transportation, Food, Accommodation, Utilities, Office Supplies, Software Subscriptions.
        If the expense does not clearly fit one of these categories, use "Other".

        Respond with ONLY a single minified JSON object (no markdown, no commentary) with this shape:
        {"category":"<category>","subCategory":"<short subcategory or null>","extractedAmount":<number or null>,"currency":"<ISO-4217 code or null>","merchant":"<merchant name or null>","confidenceScore":<0.0-1.0>}
        """;

    private const string Stage2SystemInstructions = """
        You are a general expense classification assistant used as a fallback when an expense does
        not clearly match official company policy categories. You have no tools available.

        Company categories for reference: Transportation, Food, Accommodation, Utilities,
        Office Supplies, Software Subscriptions. Choose the closest fitting category using your own
        judgement (for example, developer tooling or SaaS licenses belong under "Software
        Subscriptions"). Only use "Other" if truly nothing fits.

        Respond with ONLY a single minified JSON object (no markdown, no commentary) with this shape:
        {"category":"<category>","subCategory":"<short subcategory or null>","extractedAmount":<number or null>,"currency":"<ISO-4217 code or null>","merchant":"<merchant name or null>","confidenceScore":<0.0-1.0>}
        """;

    private readonly IChatClient _chatClient;
    private readonly IChatClient _toolCallingChatClient;
    private readonly CompanyPolicyTool _policyTool;
    private readonly SpendingLimitTool _spendingLimitTool;
    private readonly IMemoryCache _cache;
    private readonly ILogger<ExpenseClassifierAgent> _logger;
    private readonly ExpenseClassifierOptions _options;

    private readonly ChatOptions _stage1Options;
    private readonly ChatOptions _stage2Options;

    private readonly ConcurrentDictionary<string, SemaphoreSlim> _cacheKeyLocks = new();

    public ExpenseClassifierAgent(
        IChatClient chatClient,
        CompanyPolicyTool policyTool,
        SpendingLimitTool spendingLimitTool,
        IMemoryCache cache,
        ILogger<ExpenseClassifierAgent> logger,
        IOptions<ExpenseClassifierOptions> options)
    {
        _chatClient = chatClient;
        _policyTool = policyTool;
        _spendingLimitTool = spendingLimitTool;
        _cache = cache;
        _logger = logger;
        _options = options.Value;

        // Built once at startup: avoids per-request reflection over the tool methods and
        // per-request re-wrapping of the chat client's function-invocation middleware.
        _toolCallingChatClient = _chatClient.AsBuilder().UseFunctionInvocation().Build();

        var tools = new List<AITool>
        {
            AIFunctionFactory.Create(_policyTool.GetPolicy, "get_company_policy",
                "Retrieves company policy rules that define how expense descriptions map to standard corporate GL categories."),
            AIFunctionFactory.Create(_spendingLimitTool.GetSpendingLimits, "get_spending_limits",
                "Retrieves company spending thresholds and approval policies for financial compliance verification.")
        };

        _stage1Options = new ChatOptions
        {
            Tools = tools,
            Temperature = 0f,
            ResponseFormat = ChatResponseFormat.Json
        };

        _stage2Options = new ChatOptions
        {
            Temperature = 0f,
            ResponseFormat = ChatResponseFormat.Json
        };
    }

    /// <inheritdoc/>
    public async Task<ResponseDto> Classify(string expenseDescription, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(expenseDescription);

        var trimmedDescription = expenseDescription.Trim();
        var cacheKey = NormalizeCacheKey(trimmedDescription);

        if (_cache.TryGetValue(cacheKey, out ResponseDto? cached) && cached is not null)
        {
            return AsCacheHit(cached, trimmedDescription);
        }

        // Per-key gate prevents a cache stampede: concurrent requests for the same
        // (normalized) expense description share a single upstream AI invocation.
        var gate = _cacheKeyLocks.GetOrAdd(cacheKey, static _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(cancellationToken);
        try
        {
            if (_cache.TryGetValue(cacheKey, out cached) && cached is not null)
            {
                return AsCacheHit(cached, trimmedDescription);
            }

            var result = await ClassifyUncachedAsync(trimmedDescription, cancellationToken);

            _cache.Set(cacheKey, result, BuildCacheEntryOptions());

            return result;
        }
        finally
        {
            gate.Release();
        }
    }

    /// <inheritdoc/>
    public async Task<BatchExpenseResponse> ClassifyBatch(BatchExpenseRequest request, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);

        var stopwatch = Stopwatch.StartNew();
        var results = new ResponseDto[request.Items.Count];

        var maxConcurrency = Math.Max(1, _options.MaxBatchConcurrency);
        var parallelOptions = new ParallelOptions
        {
            MaxDegreeOfParallelism = maxConcurrency,
            CancellationToken = cancellationToken
        };

        await Parallel.ForEachAsync(
            Enumerable.Range(0, request.Items.Count),
            parallelOptions,
            async (index, itemCancellationToken) =>
            {
                var item = request.Items[index];
                results[index] = await Classify(item.Description, itemCancellationToken);
            });

        stopwatch.Stop();

        var summary = BuildSummary(results, stopwatch.ElapsedMilliseconds);

        return new BatchExpenseResponse
        {
            Summary = summary,
            Results = [.. results]
        };
    }

    private async Task<ResponseDto> ClassifyUncachedAsync(string expenseDescription, CancellationToken cancellationToken)
    {
        var stage1Extraction = await CallStageAsync(
            _toolCallingChatClient, Stage1SystemInstructions, _stage1Options, expenseDescription, cancellationToken);

        if (stage1Extraction is not null && IsRecognizedCategory(stage1Extraction.Category))
        {
            return BuildResponseDto(stage1Extraction, expenseDescription, "PolicyAgentWithTools");
        }

        var stage2Extraction = await CallStageAsync(
            _chatClient, Stage2SystemInstructions, _stage2Options, expenseDescription, cancellationToken);

        if (stage2Extraction is not null)
        {
            return BuildResponseDto(stage2Extraction, expenseDescription, "FallbackGeneralAgent");
        }

        if (stage1Extraction is not null)
        {
            // Both stages ran; stage 1 at least produced a parseable (if unmatched) result.
            return BuildResponseDto(stage1Extraction, expenseDescription, "PolicyAgentWithTools");
        }

        throw new UpstreamAiException(
            $"Unable to obtain a valid classification for expense description '{expenseDescription}' from either the primary or fallback AI stage.");
    }

    private async Task<ExtractionResult?> CallStageAsync(
        IChatClient client, string instructions, ChatOptions options, string expenseDescription, CancellationToken cancellationToken)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, instructions),
            new(ChatRole.User, expenseDescription)
        };

        try
        {
            var response = await client.GetResponseAsync(messages, options, cancellationToken);
            return ParseExtraction(response.Text);
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "AI classification stage failed for expense description '{Description}'.", expenseDescription);
            return null;
        }
    }

    private ExtractionResult? ParseExtraction(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return null;
        }

        var match = JsonObjectRegex.Match(text);
        var json = match.Success ? match.Value : text;

        try
        {
            return JsonSerializer.Deserialize<ExtractionResult>(json, JsonOptions);
        }
        catch (JsonException ex)
        {
            _logger.LogWarning(ex, "Failed to parse AI classification response as JSON: {Response}", text);
            return null;
        }
    }

    private static bool IsRecognizedCategory(string? category)
        => !string.IsNullOrWhiteSpace(category) && KnownCategories.Contains(category.Trim());

    private static ResponseDto BuildResponseDto(ExtractionResult extraction, string originalDescription, string stage)
    {
        var category = string.IsNullOrWhiteSpace(extraction.Category) ? "Other" : extraction.Category.Trim();
        var currency = string.IsNullOrWhiteSpace(extraction.Currency) ? null : extraction.Currency.Trim().ToUpperInvariant();

        var (complianceStatus, complianceNotes) = ComplianceEvaluator.Evaluate(category, extraction.ExtractedAmount, currency);

        return new ResponseDto
        {
            Category = category,
            SubCategory = string.IsNullOrWhiteSpace(extraction.SubCategory) ? null : extraction.SubCategory.Trim(),
            ExtractedAmount = extraction.ExtractedAmount,
            Currency = currency,
            Merchant = string.IsNullOrWhiteSpace(extraction.Merchant) ? null : extraction.Merchant.Trim(),
            ConfidenceScore = extraction.ConfidenceScore is > 0.0 and <= 1.0
                ? extraction.ConfidenceScore.Value
                : (stage == "PolicyAgentWithTools" ? 0.9 : 0.75),
            ComplianceStatus = complianceStatus,
            ComplianceNotes = complianceNotes,
            ClassificationStage = stage,
            ExpenseDescription = originalDescription
        };
    }

    private static ResponseDto AsCacheHit(ResponseDto cached, string currentDescription) => new()
    {
        Category = cached.Category,
        SubCategory = cached.SubCategory,
        ExtractedAmount = cached.ExtractedAmount,
        Currency = cached.Currency,
        Merchant = cached.Merchant,
        ConfidenceScore = cached.ConfidenceScore,
        ComplianceStatus = cached.ComplianceStatus,
        ComplianceNotes = cached.ComplianceNotes,
        ClassificationStage = "CacheHit",
        ExpenseDescription = currentDescription
    };

    private static BatchSummary BuildSummary(IReadOnlyList<ResponseDto> results, long elapsedMs)
    {
        var summary = new BatchSummary
        {
            TotalItems = results.Count,
            ProcessingTimeMs = elapsedMs
        };

        foreach (var result in results)
        {
            switch (result.ComplianceStatus)
            {
                case "Compliant":
                    summary.CompliantCount++;
                    break;
                case "RequiresManagerApproval":
                    summary.RequiresApprovalCount++;
                    break;
                case "PolicyViolation":
                    summary.PolicyViolationCount++;
                    break;
            }

            if (result.ExtractedAmount is { } amount && !string.IsNullOrWhiteSpace(result.Currency))
            {
                summary.TotalAmountByCurrency[result.Currency] =
                    summary.TotalAmountByCurrency.TryGetValue(result.Currency, out var existing)
                        ? existing + amount
                        : amount;
            }
        }

        return summary;
    }

    private MemoryCacheEntryOptions BuildCacheEntryOptions()
    {
        var duration = TimeSpan.FromMinutes(Math.Max(1, _options.CacheDurationMinutes));
        var slidingWindow = TimeSpan.FromMinutes(Math.Min(10, Math.Max(1, _options.CacheDurationMinutes)));

        return new MemoryCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = duration,
            SlidingExpiration = slidingWindow
        };
    }

    /// <summary>
    /// Normalizes an expense description into a stable cache key: trims, lowercases, collapses
    /// whitespace, and strips punctuation so near-identical descriptions share a cache entry.
    /// </summary>
    private static string NormalizeCacheKey(string expenseDescription)
    {
        var lower = expenseDescription.Trim().ToLowerInvariant();
        var withoutPunctuation = Regex.Replace(lower, @"[^\p{L}\p{N}\s]", " ");
        var collapsed = Regex.Replace(withoutPunctuation, @"\s+", " ").Trim();
        return $"expense:{collapsed}";
    }

    private sealed record ExtractionResult(
        string? Category,
        string? SubCategory,
        decimal? ExtractedAmount,
        string? Currency,
        string? Merchant,
        double? ConfidenceScore);
}
