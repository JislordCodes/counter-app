using Azure.AI.OpenAI;
using ExpenseClassifier.Agents;
using ExpenseClassifier.Models;
using ExpenseClassifier.Options;
using ExpenseClassifier.Services;
using ExpenseClassifier.Tools;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;

var builder = WebApplication.CreateBuilder(args);

// --- Candidate Assessment: Dependency Injection & Services Setup ---

builder.Services.AddProblemDetails();

builder.Services.Configure<ExpenseClassifierOptions>(
    builder.Configuration.GetSection(ExpenseClassifierOptions.SectionName));

builder.Services.AddMemoryCache();

// Stateless, thread-safe tool wrappers: safe to share for the lifetime of the app.
builder.Services.AddSingleton<CompanyPolicyTool>();
builder.Services.AddSingleton<SpendingLimitTool>();

var useSimulation = builder.Configuration.GetValue<bool>($"{ExpenseClassifierOptions.SectionName}:UseSimulation");
if (useSimulation)
{
    builder.Services.AddSingleton<IChatClient, SimulationChatClient>();
}
else
{
    // AzureOpenAIClient and the IChatClient wrapping it are thread-safe and hold pooled
    // connections; registering them as singletons avoids a new client (and TCP/TLS setup)
    // per request (a captive-dependency/performance trap for a Scoped registration here,
    // since the agent that consumes them is itself a singleton).
    builder.Services.AddSingleton(sp =>
    {
        var config = sp.GetRequiredService<IConfiguration>();
        var endpoint = config["AzureOpenAI:Endpoint"] ?? throw new InvalidOperationException("AzureOpenAI:Endpoint is not configured.");
        var apiKey = config["AzureOpenAI:ApiKey"] ?? throw new InvalidOperationException("AzureOpenAI:ApiKey is not configured.");

        return new AzureOpenAIClient(new Uri(endpoint), new System.ClientModel.ApiKeyCredential(apiKey));
    });

    builder.Services.AddSingleton<IChatClient>(sp =>
    {
        var config = sp.GetRequiredService<IConfiguration>();
        var deploymentName = config["AzureOpenAI:DeploymentName"] ?? throw new InvalidOperationException("AzureOpenAI:DeploymentName is not configured.");

        var client = sp.GetRequiredService<AzureOpenAIClient>();
        return client.GetChatClient(deploymentName).AsIChatClient();
    });
}

// The agent pre-builds its tool-calling chat client, AIFunction wrappers, and ChatOptions once
// in its constructor, so it is registered as a singleton to reuse that setup across requests.
builder.Services.AddSingleton<IExpenseClassifierAgent, ExpenseClassifierAgent>();

var app = builder.Build();

app.UseExceptionHandler(errorApp => errorApp.Run(async context =>
{
    var feature = context.Features.Get<Microsoft.AspNetCore.Diagnostics.IExceptionHandlerFeature>();
    var isUpstreamFailure = feature?.Error is UpstreamAiException;

    context.Response.StatusCode = isUpstreamFailure ? StatusCodes.Status502BadGateway : StatusCodes.Status500InternalServerError;
    await Results.Problem(
        title: isUpstreamFailure ? "Upstream AI Service Failure" : "Internal Server Error",
        detail: isUpstreamFailure ? feature!.Error.Message : "An unexpected error occurred while processing the request.",
        statusCode: context.Response.StatusCode
    ).ExecuteAsync(context);
}));

// --- API Endpoints ---

// Single Expense Classification Endpoint
app.MapPost("/classify", async (IExpenseClassifierAgent agent, RequestDto request, CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request?.Description))
    {
        return Results.BadRequest(new ProblemDetails
        {
            Title = "Invalid Request Payload",
            Detail = "Expense description must not be empty or whitespace.",
            Status = StatusCodes.Status400BadRequest
        });
    }

    var result = await agent.Classify(request.Description, cancellationToken);
    return Results.Ok(result);
});

// Batch Expense Classification Endpoint
app.MapPost("/classify/batch", async (IExpenseClassifierAgent agent, BatchExpenseRequest request, CancellationToken cancellationToken) =>
{
    if (request?.Items == null || request.Items.Count == 0)
    {
        return Results.BadRequest(new ProblemDetails
        {
            Title = "Invalid Batch Request Payload",
            Detail = "Batch items list cannot be null or empty.",
            Status = StatusCodes.Status400BadRequest
        });
    }

    var invalidItem = request.Items.FirstOrDefault(item => string.IsNullOrWhiteSpace(item.Description));
    if (invalidItem is not null)
    {
        return Results.BadRequest(new ProblemDetails
        {
            Title = "Invalid Batch Item Payload",
            Detail = $"Batch item '{invalidItem.Id ?? "(no id)"}' has an empty or whitespace description.",
            Status = StatusCodes.Status400BadRequest
        });
    }

    var result = await agent.ClassifyBatch(request, cancellationToken);
    return Results.Ok(result);
});

await app.RunAsync();
