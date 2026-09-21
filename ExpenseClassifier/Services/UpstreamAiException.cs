namespace ExpenseClassifier.Services;

/// <summary>
/// Thrown when the upstream AI chat client fails, times out, or returns a response that
/// cannot be parsed into a usable classification after all retries/fallback stages are exhausted.
/// Mapped to an RFC 7807 502 Bad Gateway <c>ProblemDetails</c> response at the API boundary.
/// </summary>
public class UpstreamAiException : Exception
{
    public UpstreamAiException(string message, Exception? innerException = null)
        : base(message, innerException)
    {
    }
}
