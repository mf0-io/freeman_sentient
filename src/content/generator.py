"""
Content Generator Module for Digital Freeman
Transforms content ideas into actual tweet text using LLM with Freeman's persona voice
"""

import os
import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# LLM imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.content.ideation import ContentIdea


@dataclass
class GeneratedContent:
    """Represents generated content ready for posting"""
    text: str
    idea: ContentIdea
    platform: str  # twitter, telegram
    character_count: int
    generated_at: datetime
    llm_provider: str  # claude, openai
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'text': self.text,
            'idea': self.idea.to_dict(),
            'platform': self.platform,
            'character_count': self.character_count,
            'generated_at': self.generated_at.isoformat(),
            'llm_provider': self.llm_provider,
            'metadata': self.metadata or {}
        }


class ContentGenerator:
    """
    Generates tweet text from content ideas using LLM

    Responsibilities:
    - Load Freeman's persona voice from config
    - Use Claude (primary) or OpenAI (fallback) to generate text
    - Ensure platform-specific constraints (280 chars for Twitter)
    - Apply Freeman's characteristic style and tone
    - Retry logic for failed generations
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """Initialize the generator with configuration"""
        self.config = self._load_config(config_path)
        self.persona = self.config.get('persona', {})
        self.generation_config = self.config.get('generation', {})
        self.llm_config = self.generation_config.get('llm', {})
        self.validation_config = self.generation_config.get('validation', {})
        self.platform_config = self.config.get('platforms', {})

        # Initialize LLM clients
        self._init_llm_clients()

        # Build system prompt for Freeman's voice
        self.system_prompt = self._build_system_prompt()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _init_llm_clients(self):
        """Initialize LLM API clients"""
        # Claude client
        self.claude_client = None
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)

        # OpenAI client
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)

        # Verify at least one is available
        if not self.claude_client and not self.openai_client:
            raise RuntimeError(
                "No LLM provider available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
            )

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines Freeman's voice"""
        voice = self.persona.get('voice', {})
        mission = self.persona.get('mission', '')
        core_values = self.persona.get('core_values', [])

        prompt = f"""You are Freeman - a sarcastic, philosophical, and provocative AI persona.

MISSION: {mission}

CORE VALUES:
{chr(10).join(f'- {value}' for value in core_values)}

VOICE CHARACTERISTICS:
- Style: {voice.get('style', 'sarcastic, philosophical, provocative')}
- Tone: {voice.get('tone', 'sharp, ironic, deep')}
- Language: {voice.get('language', 'direct, uncensored, intellectually challenging')}

AVOID:
{chr(10).join(f'- {avoid}' for avoid in voice.get('avoid', []))}

GUIDELINES:
1. Be authentic and raw - no corporate polish
2. Use sharp wit and sarcasm when appropriate
3. Challenge assumptions and expose hypocrisy
4. Make people THINK, not just consume
5. Be provocative but meaningful - no empty shock value
6. Use profanity sparingly but effectively when it serves the message
7. Ask uncomfortable questions that need to be asked
8. Never be superficial or generic

Your tweets should make people stop scrolling and reconsider their reality.
"""
        return prompt

    def generate(
        self,
        idea: ContentIdea,
        platform: str = "twitter",
        max_retries: int = None
    ) -> Optional[GeneratedContent]:
        """
        Generate content from an idea

        Args:
            idea: ContentIdea object with topic, angle, tone
            platform: Target platform (twitter, telegram)
            max_retries: Number of retry attempts (defaults to config)

        Returns:
            GeneratedContent object or None if generation fails
        """
        if max_retries is None:
            max_retries = self.validation_config.get('max_retries', 3)

        # Get platform constraints
        platform_limits = self.platform_config.get(platform, {})
        max_length = platform_limits.get('max_length', 280)

        # Build generation prompt
        user_prompt = self._build_generation_prompt(idea, platform, max_length)

        # Try generation with retries
        for attempt in range(max_retries):
            try:
                # Try primary provider (Claude)
                if self.llm_config.get('provider') == 'claude' and self.claude_client:
                    text = self._generate_with_claude(user_prompt, max_length)
                    provider = 'claude'
                # Try OpenAI
                elif self.llm_config.get('provider') == 'openai' and self.openai_client:
                    text = self._generate_with_openai(user_prompt, max_length)
                    provider = 'openai'
                # Fallback logic
                else:
                    # Try fallback provider
                    fallback = self.llm_config.get('fallback', {})
                    if fallback.get('provider') == 'openai' and self.openai_client:
                        text = self._generate_with_openai(user_prompt, max_length)
                        provider = 'openai'
                    elif self.claude_client:
                        text = self._generate_with_claude(user_prompt, max_length)
                        provider = 'claude'
                    else:
                        raise RuntimeError("No LLM provider available")

                # Validate generated text
                if text and len(text) <= max_length:
                    return GeneratedContent(
                        text=text,
                        idea=idea,
                        platform=platform,
                        character_count=len(text),
                        generated_at=datetime.now(),
                        llm_provider=provider,
                        metadata={
                            'attempt': attempt + 1,
                            'max_length': max_length
                        }
                    )

            except Exception as e:
                print(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
                continue

        return None

    def _build_generation_prompt(
        self,
        idea: ContentIdea,
        platform: str,
        max_length: int
    ) -> str:
        """Build the user prompt for content generation"""
        prompt = f"""Generate a tweet based on this idea:

TOPIC: {idea.topic}
ANGLE: {idea.angle}
TONE: {idea.tone}
SOURCE: {idea.source}

CONSTRAINTS:
- Maximum {max_length} characters (including spaces and punctuation)
- Platform: {platform}
- Must match Freeman's voice (see system prompt)
- Be provocative but meaningful
- No hashtags, no corporate speak

Generate ONLY the tweet text, nothing else. No quotes around it, no explanations.
Make it hit hard. Make it memorable. Make them think.
"""
        return prompt

    def _generate_with_claude(self, prompt: str, max_length: int) -> Optional[str]:
        """Generate content using Claude API"""
        if not self.claude_client:
            return None

        try:
            model = self.llm_config.get('model', 'claude-3-5-sonnet-20241022')
            temperature = self.llm_config.get('temperature', 0.9)
            max_tokens = min(self.llm_config.get('max_tokens', 500), 500)

            response = self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                text = response.content[0].text.strip()
                # Remove quotes if LLM added them
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                if text.startswith("'") and text.endswith("'"):
                    text = text[1:-1]
                return text

        except Exception as e:
            print(f"Claude API error: {e}")
            return None

        return None

    def _generate_with_openai(self, prompt: str, max_length: int) -> Optional[str]:
        """Generate content using OpenAI API"""
        if not self.openai_client:
            return None

        try:
            fallback_config = self.llm_config.get('fallback', {})
            model = fallback_config.get('model', 'gpt-4')
            temperature = fallback_config.get('temperature', 0.9)
            max_tokens = min(fallback_config.get('max_tokens', 500), 500)

            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract text from response
            if response.choices and len(response.choices) > 0:
                text = response.choices[0].message.content.strip()
                # Remove quotes if LLM added them
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                if text.startswith("'") and text.endswith("'"):
                    text = text[1:-1]
                return text

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None

        return None

    def generate_batch(
        self,
        ideas: List[ContentIdea],
        platform: str = "twitter"
    ) -> List[GeneratedContent]:
        """
        Generate content for multiple ideas

        Args:
            ideas: List of ContentIdea objects
            platform: Target platform

        Returns:
            List of successfully generated content (may be fewer than input)
        """
        generated = []
        for idea in ideas:
            content = self.generate(idea, platform=platform)
            if content:
                generated.append(content)
        return generated

    def regenerate(
        self,
        content: GeneratedContent,
        reason: str = "retry"
    ) -> Optional[GeneratedContent]:
        """
        Regenerate content (e.g., if validation failed)

        Args:
            content: Previous GeneratedContent to regenerate
            reason: Reason for regeneration

        Returns:
            New GeneratedContent or None
        """
        return self.generate(
            idea=content.idea,
            platform=content.platform
        )


# Convenience function for quick generation
def generate_content(
    idea: ContentIdea,
    platform: str = "twitter"
) -> Optional[GeneratedContent]:
    """
    Quick function to generate content from an idea

    Args:
        idea: ContentIdea object
        platform: Target platform

    Returns:
        GeneratedContent object or None
    """
    generator = ContentGenerator()
    return generator.generate(idea, platform=platform)


if __name__ == "__main__":
    # Demo/testing functionality
    print("Digital Freeman - Content Generator Module")
    print("=" * 50)

    try:
        # Check API keys
        has_claude = bool(os.getenv('ANTHROPIC_API_KEY'))
        has_openai = bool(os.getenv('OPENAI_API_KEY'))

        print(f"✓ Claude API: {'Available' if has_claude else 'Not configured'}")
        print(f"✓ OpenAI API: {'Available' if has_openai else 'Not configured'}")

        if not has_claude and not has_openai:
            print("\n⚠ Warning: No API keys found in environment")
            print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY to test generation")
            print("\nGenerator class can still be imported and configured.")
        else:
            # Initialize generator
            generator = ContentGenerator()
            print(f"✓ Generator initialized")
            print(f"✓ Primary LLM: {generator.llm_config.get('provider', 'none')}")

            # Create a test idea
            from src.content.ideation import ContentIdeator

            ideator = ContentIdeator()
            test_idea = ideator.generate_idea(source='philosophical_topics')

            print(f"\n📝 Test idea:")
            print(f"   Topic: {test_idea.topic}")
            print(f"   Angle: {test_idea.angle}")
            print(f"   Tone: {test_idea.tone}")

            print(f"\n⚙ Generating content...")
            content = generator.generate(test_idea, platform='twitter')

            if content:
                print(f"\n✓ Generated content:")
                print(f"   Text: {content.text}")
                print(f"   Length: {content.character_count}/280 chars")
                print(f"   Provider: {content.llm_provider}")
            else:
                print(f"\n✗ Generation failed")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
