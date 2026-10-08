"""Value-free transformation publication diagnostics shared by adapters."""

class TransformationPublicationError(ValueError):
    """Value-free failure in private temporary publication."""


CLEANUP_INCOMPLETE_MESSAGE = (
    "transformation publication failed; cleanup incomplete; output or staging may remain; "
    "inspect the selected destination before retrying"
)


class TransformationCleanupError(TransformationPublicationError):
    """Publication failed and artifact removal could not be confirmed."""


