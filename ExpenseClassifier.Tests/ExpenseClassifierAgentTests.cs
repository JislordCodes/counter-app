using ExpenseClassifier.Agents;
using ExpenseClassifier.Models;
using ExpenseClassifier.Options;
using ExpenseClassifier.Services;
using ExpenseClassifier.Tools;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ExpenseClassifier.Tests;

public class ExpenseClassifierAgentTests
{
    private static ExpenseClassifierAgent CreateAgent(int maxBatchConcurrency = 5, IMemoryCache? cache = null)
    {
        var options = Microsoft.Extensions.Options.Options.Create(new ExpenseClassifierOptions
        {
            UseSimulation = true,
            CacheDurationMinutes = 30,
            MaxBatchConcurrency = maxBatchConcurrency
        });

        return new ExpenseClassifierAgent(
            new SimulationChatClient(),
            new CompanyPolicyTool(),
            new SpendingLimitTool(),
            cache ?? new MemoryCache(new MemoryCacheOptions()),
            NullLogger<ExpenseClassifierAgent>.Instance,
            options);
    }

    [Fact]
    public async Task Classify_PolicyMatch_ReturnsPolicyAgentWithToolsStage()
    {
        var agent = CreateAgent();

        var result = await agent.Classify("Bolt ride from Murtala Muhammed Airport to Victoria Island costing ₦15,000");

        Assert.Equal("Transportation", result.Category);
        Assert.Equal("Bolt", result.Merchant);
        Assert.Equal("PolicyAgentWithTools", result.ClassificationStage);
        Assert.Equal("Compliant", result.ComplianceStatus);
    }

    [Fact]
    public async Task Classify_UnmatchedPolicyCategory_FallsBackToGeneralAgent()
    {
        var agent = CreateAgent();

        var result = await agent.Classify("Annual JetBrains Rider IDE team license renewal for software engineers $650 USD");

        Assert.Equal("Software Subscriptions", result.Category);
        Assert.Equal("JetBrains", result.Merchant);
        Assert.Equal("FallbackGeneralAgent", result.ClassificationStage);
    }

    [Fact]
    public async Task Classify_SecondCallWithSameNormalizedDescription_IsCacheHit()
    {
        var agent = CreateAgent();

        var first = await agent.Classify("  Bolt ride to Victoria Island costing ₦8,500  ");
        var second = await agent.Classify("bolt RIDE to victoria island costing ₦8,500");

        Assert.Equal("PolicyAgentWithTools", first.ClassificationStage);
        Assert.Equal("CacheHit", second.ClassificationStage);
        Assert.Equal(first.Category, second.Category);
        Assert.Equal(first.ExtractedAmount, second.ExtractedAmount);
        // The cache hit still echoes back the caller's own input text, not the first call's.
        Assert.Equal("bolt RIDE to victoria island costing ₦8,500", second.ExpenseDescription);
    }

    [Fact]
    public async Task Classify_WhenAmountMissing_IsUnverifiableAndStillCacheable()
    {
        var agent = CreateAgent();

        var first = await agent.Classify("Bolt ride from Airport to office");
        var second = await agent.Classify("Bolt ride from Airport to office");

        Assert.Equal("Unverifiable", first.ComplianceStatus);
        Assert.Equal("CacheHit", second.ClassificationStage);
    }

    [Fact]
    public async Task ClassifyBatch_AggregatesSummaryAcrossCurrenciesAndStatuses()
    {
        var agent = CreateAgent();

        var request = new BatchExpenseRequest
        {
            Department = "Engineering",
            EmployeeId = "EMP-9402",
            Items =
            [
                new ExpenseItemRequest { Id = "1", Description = "Bolt ride to office ₦8,500" },
                new ExpenseItemRequest { Id = "2", Description = "Team lunch at Bukka Hut ₦42,000" },
                new ExpenseItemRequest { Id = "3", Description = "Monthly MTN 5G Broadband data subscription ₦35,000" },
                new ExpenseItemRequest { Id = "4", Description = "GitHub Copilot monthly subscription $19 USD" }
            ]
        };

        var response = await agent.ClassifyBatch(request);

        Assert.Equal(4, response.Summary.TotalItems);
        Assert.Equal(3, response.Summary.CompliantCount);
        Assert.Equal(1, response.Summary.RequiresApprovalCount);
        Assert.Equal(0, response.Summary.PolicyViolationCount);
        Assert.Equal(85500m, response.Summary.TotalAmountByCurrency["NGN"]);
        Assert.Equal(19m, response.Summary.TotalAmountByCurrency["USD"]);
        Assert.Equal(4, response.Results.Count);
        // Batch results preserve request order.
        Assert.Equal("1", request.Items[0].Id);
        Assert.Equal("Transportation", response.Results[0].Category);
        Assert.Equal("Software Subscriptions", response.Results[3].Category);
    }

    [Fact]
    public async Task ClassifyBatch_RespectsBoundedConcurrency()
    {
        var agent = CreateAgent(maxBatchConcurrency: 2);

        var request = new BatchExpenseRequest
        {
            Items = Enumerable.Range(1, 10)
                .Select(i => new ExpenseItemRequest { Id = i.ToString(), Description = $"Bolt ride #{i} to office ₦{i}000" })
                .ToList()
        };

        var response = await agent.ClassifyBatch(request);

        Assert.Equal(10, response.Summary.TotalItems);
        Assert.All(response.Results, r => Assert.Equal("Transportation", r.Category));
    }

    [Fact]
    public async Task Classify_NullOrWhitespaceDescription_Throws()
    {
        var agent = CreateAgent();

        await Assert.ThrowsAsync<ArgumentException>(() => agent.Classify(""));
        await Assert.ThrowsAsync<ArgumentException>(() => agent.Classify("   "));
    }
}
