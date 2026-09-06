class CapturingLLM:
    def __init__(self, response: str) -> None:
        self.response = response
        self.user_prompt = None

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        **kwargs,
    ) -> str:
        self.user_prompt = user_prompt
        return self.response
