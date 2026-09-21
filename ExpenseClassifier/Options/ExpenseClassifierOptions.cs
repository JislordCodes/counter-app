namespace ExpenseClassifier.Options;

/// <summary>
/// Strongly typed configuration bound from the "ExpenseClassifier" configuration section.
/// </summary>
public class ExpenseClassifierOptions
{
    public const string SectionName = "ExpenseClassifier";

    public bool UseSimulation { get; set; }

    public int CacheDurationMinutes { get; set; } = 30;

    public int MaxBatchConcurrency { get; set; } = 5;
}
