import sys
from unittest.mock import patch


def pytest_configure(config):
    """Ensure the local mdformat-pandoc plugin is registered in mdformat."""
    import mdformat.plugins

    import mdformat_pandoc

    # ALWAYS inject our local plugin into mdformat's parser extension registry.
    # This ensures that even if a version is installed in the environment (e.g. Nix store),
    # we use the local code under test.
    print("DEBUG: Force injecting local pandoc plugin into mdformat.plugins", file=sys.stderr)

    # Pre-emptively patch entry_points before mdformat.plugins uses it

    class MockDist:
        def __init__(self):
            self.version = "0.1.0"
            self.name = "mdformat-pandoc"
            self.metadata = {"Name": "mdformat-pandoc"}

    class MockEntryPoint:
        def __init__(self, name, value, group):
            self.name = name
            self.value = value
            self.group = group
            self.dist = MockDist()

        def load(self):
            return mdformat_pandoc

    def mocked_entry_points(**kwargs):
        group = kwargs.get("group")
        if group == "mdformat.parser_extension":
            return [MockEntryPoint("pandoc", "mdformat_pandoc", "mdformat.parser_extension")]
        if group == "mdformat.renderer":
            # mdformat 1.x doesn't use this but older versions might
            return [MockEntryPoint("pandoc", "mdformat_pandoc", "mdformat.renderer")]
        return []

    # Apply the patch globally for the test process
    patcher = patch("importlib.metadata.entry_points", side_effect=mocked_entry_points)
    patcher.start()

    # If PARSER_EXTENSIONS was already initialized, we must update it
    try:
        mdformat.plugins.PARSER_EXTENSIONS["pandoc"] = mdformat_pandoc
    except Exception as e:
        print(f"DEBUG: Could not directly update PARSER_EXTENSIONS: {e}", file=sys.stderr)
