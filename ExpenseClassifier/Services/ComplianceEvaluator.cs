namespace ExpenseClassifier.Services;

/// <summary>
/// Deterministic, code-driven evaluation of <see cref="Tools.SpendingLimitTool"/> thresholds.
/// Shared by the live agent pipeline and <see cref="SimulationChatClient"/> so that compliance
/// verdicts never depend on the AI model correctly performing threshold arithmetic itself.
/// </summary>
public static class ComplianceEvaluator
{
    public static (string Status, string? Notes) Evaluate(string category, decimal? amount, string? currency)
    {
        if (amount is null)
        {
            return ("Unverifiable", "Amount not specified in expense description; unable to verify threshold compliance.");
        }

        var amt = amount.Value;
        var isNgn = string.Equals(currency, "NGN", StringComparison.OrdinalIgnoreCase);
        var isUsd = string.Equals(currency, "USD", StringComparison.OrdinalIgnoreCase);

        return category switch
        {
            "Food" when (isNgn && amt > 100000) || (isUsd && amt > 150) =>
                ("PolicyViolation", "Exceeds maximum allowable entertainment limit per policy without prior executive approval."),
            "Food" when (isNgn && amt > 35000) || (isUsd && amt > 50) =>
                ("RequiresManagerApproval", "Meal expense exceeds standard ₦35,000 / $50 per-person allowance; requires manager sign-off."),
            "Transportation" when (isNgn && amt > 50000) || (isUsd && amt > 60) =>
                ("RequiresManagerApproval", "Transit fare exceeds standard limit; requires manager justification."),
            "Accommodation" when (isNgn && amt > 300000) || (isUsd && amt > 350) =>
                ("RequiresManagerApproval", "Hotel rate exceeds standard ₦180,000 / $200 per night threshold."),
            _ => ("Compliant", "Expense is within standard company policy limits.")
        };
    }
}
