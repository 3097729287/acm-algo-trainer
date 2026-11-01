"""Shared, typed update validation errors; messages are not protocol values."""

class UpdateBaseMismatch(ValueError):
    """A trusted delta cannot be applied to this installation's exact bytes."""

class UpdateStorageError(ValueError):
    """No further update files may be written until storage is resolved."""
