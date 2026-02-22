"""
Content Validator Module for Digital Freeman
Validates that generated content matches Freeman's persona voice and rejects generic/corporate content
"""

import re
import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.content.generator import GeneratedContent


@dataclass
class ValidationResult:
    """Result of persona voice validation"""
    passed: bool
    score: float  # 0-1, overall match to Freeman's voice
    feedback: List[str]  # Specific feedback on what passed/failed
    checks: Dict[str, bool]  # Individual check results

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'passed': self.passed,
            'score': self.score,
            'feedback': self.feedback,
            'checks': self.checks
        }


class PersonaValidator:
    """
    Validates content against Freeman's persona voice

    Responsibilities:
    - Check for generic/corporate language
    - Verify authentic Freeman voice characteristics
    - Ensure mission alignment
    - Validate depth and meaning
    - Score overall persona match
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """Initialize validator with configuration"""
        self.config = self._load_config(config_path)
        self.persona = self.config.get('persona', {})
        self.validation_config = self.config.get('generation', {}).get('validation', {})

        # Validation thresholds
        self.threshold = self.validation_config.get('persona_match_threshold', 0.7)
        self.reject_generic = self.validation_config.get('reject_generic', True)
        self.reject_corporate = self.validation_config.get('reject_corporate', True)

        # Freeman's voice characteristics
        self.voice = self.persona.get('voice', {})
        self.avoid_list = self.voice.get('avoid', [])
        self.mission = self.persona.get('mission', '')
        self.core_values = self.persona.get('core_values', [])

        # Compile rejection patterns
        self._compile_patterns()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _compile_patterns(self):
        """Compile regex patterns for content rejection"""
        # Corporate speak patterns
        self.corporate_patterns = [
            r'\b(synergy|leverage|paradigm|disrupt|innovate|optimize)\b',
            r'\b(utilize|facilitate|implement|streamline|maximize)\b',
            r'\b(value-add|game-changer|thought leader|best practices)\b',
            r'\b(circle back|touch base|reach out|loop in)\b',
            r'\b(low-hanging fruit|move the needle|win-win)\b'
        ]

        # Generic motivational patterns
        self.generic_patterns = [
            r'\b(believe in yourself|follow your dreams|never give up)\b',
            r'\b(you can do it|stay positive|good vibes only)\b',
            r'\b(hustle harder|grind never stops|success mindset)\b',
            r'\b(manifest|blessed|grateful|abundance)\b',
            r'\b(inspirational|motivational) quote\b'
        ]

        # Superficial positivity patterns
        self.superficial_patterns = [
            r'^\s*\u2728',  # Starts with sparkle emoji
            r'\u2764\ufe0f',  # Heart emoji
            r'\U0001F64F',  # Prayer hands
            r'\U0001F496',  # Sparkling heart
            r'\b(amazing|awesome|incredible|fantastic)\s+(day|life|journey)\b',
            r'\b(amazing|awesome) (vibes?|energy)\b',
            r'\b(stay|keep|be) positive\b',
            r'\bgood vibes only\b'
        ]

    def validate(self, content: GeneratedContent) -> ValidationResult:
        """
        Validate content against Freeman's persona

        Args:
            content: GeneratedContent object to validate

        Returns:
            ValidationResult with pass/fail and detailed feedback
        """
        text = content.text.lower()
        feedback = []
        checks = {}
        scores = []

        # Check 1: Reject corporate speak
        if self.reject_corporate:
            has_corporate, corporate_feedback = self._check_corporate_speak(text)
            checks['no_corporate_speak'] = not has_corporate
            if has_corporate:
                feedback.append(corporate_feedback)
                scores.append(0.0)
            else:
                scores.append(1.0)

        # Check 2: Reject generic content
        if self.reject_generic:
            is_generic, generic_feedback = self._check_generic_content(text)
            checks['no_generic_content'] = not is_generic
            if is_generic:
                feedback.append(generic_feedback)
                scores.append(0.0)
            else:
                scores.append(1.0)

        # Check 3: Check for superficial positivity
        is_superficial, superficial_feedback = self._check_superficial_positivity(text)
        checks['no_superficial_positivity'] = not is_superficial
        if is_superficial:
            feedback.append(superficial_feedback)
            scores.append(0.0)
        else:
            scores.append(1.0)

        # Check 4: Has unique perspective (not generic statement)
        has_perspective, perspective_score = self._check_unique_perspective(content.text)
        checks['has_unique_perspective'] = has_perspective
        if not has_perspective:
            feedback.append("Content lacks unique perspective or insight")
        scores.append(perspective_score)

        # Check 5: Has depth (not superficial)
        has_depth, depth_score = self._check_depth(content.text)
        checks['not_superficial'] = has_depth
        if not has_depth:
            feedback.append("Content is too superficial or simplistic")
        scores.append(depth_score)

        # Check 6: Mission alignment
        mission_aligned, mission_score = self._check_mission_alignment(content)
        checks['matches_mission'] = mission_aligned
        if not mission_aligned:
            feedback.append("Content doesn't align with Freeman's mission")
        scores.append(mission_score)

        # Check 7: Provocative but meaningful
        is_meaningful, meaningful_score = self._check_meaningful_provocation(content.text)
        checks['provocative_but_meaningful'] = is_meaningful
        if not is_meaningful:
            feedback.append("Content lacks meaningful provocation")
        scores.append(meaningful_score)

        # Check 8: No empty platitudes
        no_platitudes, platitude_score = self._check_no_platitudes(text)
        checks['no_empty_platitudes'] = no_platitudes
        if not no_platitudes:
            feedback.append("Content contains empty platitudes")
        scores.append(platitude_score)

        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Determine pass/fail
        passed = overall_score >= self.threshold and all([
            checks.get('no_corporate_speak', True),
            checks.get('no_generic_content', True),
            checks.get('no_superficial_positivity', True)
        ])

        # Add success feedback if passed
        if passed:
            feedback.append(f"Content matches Freeman's voice (score: {overall_score:.2f})")

        return ValidationResult(
            passed=passed,
            score=overall_score,
            feedback=feedback,
            checks=checks
        )

    def _check_corporate_speak(self, text: str) -> Tuple[bool, str]:
        """Check for corporate language"""
        for pattern in self.corporate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                return True, f"Contains corporate speak: '{match.group()}'"
        return False, ""

    def _check_generic_content(self, text: str) -> Tuple[bool, str]:
        """Check for generic motivational content"""
        for pattern in self.generic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                return True, f"Contains generic motivational language: '{match.group()}'"
        return False, ""

    def _check_superficial_positivity(self, text: str) -> Tuple[bool, str]:
        """Check for superficial positivity"""
        for pattern in self.superficial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, "Contains superficial positivity (emojis or clichés)"
        return False, ""

    def _check_unique_perspective(self, text: str) -> Tuple[bool, float]:
        """
        Check if content has a unique perspective
        Freeman should challenge assumptions, not state obvious facts
        """
        # Indicators of unique perspective
        unique_indicators = [
            r'\?',  # Questions
            r'\b(nobody|no one|everyone)\b.*\b(want|tell|ask|know)',  # Challenging what's accepted
            r'\b(real|actual|true|hidden|underlying)\b',  # Diving deeper
            r'\b(illusion|paradox|irony|absurd)\b',  # Freeman's philosophical terms
            r'\b(but|yet|however|meanwhile)\b',  # Contrasts and contradictions
            r'\b(why|how|what if|imagine)\b'  # Provocative questioning
        ]

        matches = 0
        for indicator in unique_indicators:
            if re.search(indicator, text, re.IGNORECASE):
                matches += 1

        # Score based on number of unique perspective indicators
        score = min(matches / 3.0, 1.0)  # 3+ indicators = full score
        has_perspective = score >= 0.33  # At least 1 indicator

        return has_perspective, score

    def _check_depth(self, text: str) -> Tuple[bool, float]:
        """
        Check if content has intellectual depth
        Freeman doesn't do surface-level takes
# Integration point: analytics hooks
        """
        # Depth indicators
        depth_indicators = [
            r'\b(system|structure|mechanism|pattern|design)\b',  # Systems thinking
            r'\b(consciousness|perception|reality|truth|awareness)\b',  # Deep concepts
            r'\b(control|manipulate|exploit|condition|program)\b',  # Power dynamics
            r'\b(question|examine|analyze|consider|reflect)\b',  # Critical thinking
            r'\b(beneath|behind|beyond|under|within)\b'  # Looking deeper
        ]

        # Check length (very short = likely superficial)
        words = text.split()
        if len(words) < 10:
            length_score = 0.3
        elif len(words) < 20:
            length_score = 0.7
        else:
            length_score = 1.0

        # Check depth indicators
        matches = 0
        for indicator in depth_indicators:
            if re.search(indicator, text, re.IGNORECASE):
                matches += 1

        indicator_score = min(matches / 2.0, 1.0)  # 2+ indicators = full score

        # Combined score
        score = (length_score + indicator_score) / 2.0
        has_depth = score >= 0.5

        return has_depth, score

    def _check_mission_alignment(self, content: GeneratedContent) -> Tuple[bool, float]:
        """
        Check if content aligns with Freeman's mission
        Mission: Awaken people, expose truth, teach consciousness hygiene
        """
        text = content.text.lower()
        idea_topic = content.idea.topic.lower() if content.idea else ""

        # Mission keywords
        mission_keywords = [
            'awaken', 'wake up', 'see', 'realize', 'understand', 'truth',
            'consciousness', 'aware', 'question', 'ask', 'think', 'examine',
            'control', 'manipulate', 'system', 'propaganda', 'illusion',
            'freedom', 'independent', 'critical', 'hygiene', 'mind'
        ]

        # Check content and idea topic
        combined_text = text + " " + idea_topic
        matches = sum(1 for keyword in mission_keywords if keyword in combined_text)

        # Score based on mission keyword density
        words = combined_text.split()
        if len(words) > 0:
            density = matches / max(len(words), 10)  # Normalize by length
            score = min(density * 5, 1.0)  # 5x multiplier for mission alignment
        else:
            score = 0.0

        # Priority topics get bonus
        if content.idea and content.idea.category == 'priority':
            score = min(score + 0.2, 1.0)

        aligned = score >= 0.4
        return aligned, score

    def _check_meaningful_provocation(self, text: str) -> Tuple[bool, float]:
        """
        Check if content is provocative but has meaning
        Not just shock value, but challenges thinking
        """
        # Provocation indicators
        provocation_indicators = [
            r'\?',  # Questions provoke thought
            r'\b(why|how come|ever wonder|notice)\b',  # Provocative questions
            r'\b(nobody|no one|everyone|they|you)\b',  # Direct address
            r'\b(pretend|ignore|deny|avoid|hide)\b',  # Calling out behavior
            r'\b(uncomfortable|inconvenient|unpopular|forbidden)\b',  # Taboo topics
        ]

        # Meaning indicators (different from pure shock)
        meaning_indicators = [
            r'\b(because|reason|why|how|means|reveals|shows)\b',  # Explanation
            r'\b(real|actually|truth|fact|reality)\b',  # Truth-seeking
            r'\b(understand|learn|realize|see|recognize)\b',  # Learning/growth
        ]

        provocation_score = sum(
            1 for p in provocation_indicators
            if re.search(p, text, re.IGNORECASE)
        ) / len(provocation_indicators)

        meaning_score = sum(
            1 for m in meaning_indicators
            if re.search(m, text, re.IGNORECASE)
        ) / len(meaning_indicators)

        # Both needed for meaningful provocation (but provocation weighted more heavily)
        combined_score = (provocation_score * 0.7 + meaning_score * 0.3)
        is_meaningful = combined_score >= 0.13

        return is_meaningful, combined_score

    def _check_no_platitudes(self, text: str) -> Tuple[bool, float]:
        """
        Check for empty platitudes
        Freeman doesn't do feel-good nonsense
        """
        platitude_patterns = [
            r'\b(everything happens for a reason|meant to be)\b',
            r'\b(just be yourself|be true to yourself)\b',
            r'\b(live laugh love|good vibes only)\b',
            r'\b(chase your dreams|follow your heart)\b',
            r'\b(stay positive|think positive)\b',
            r'\b(it gets better|this too shall pass)\b'
        ]

        for pattern in platitude_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, 0.0

        return True, 1.0

    def validate_batch(
        self,
        contents: List[GeneratedContent]
    ) -> List[ValidationResult]:
        """
        Validate multiple content pieces

        Args:
            contents: List of GeneratedContent to validate

        Returns:
            List of ValidationResult objects
        """
        return [self.validate(content) for content in contents]

    def get_passing_content(
        self,
        contents: List[GeneratedContent]
    ) -> List[GeneratedContent]:
        """
        Filter content to only those that pass validation

        Args:
            contents: List of GeneratedContent to filter

        Returns:
            List of GeneratedContent that passed validation
        """
        passing = []
        for content in contents:
            result = self.validate(content)
            if result.passed:
                passing.append(content)
        return passing


# Convenience function for quick validation
def validate_content(content: GeneratedContent) -> ValidationResult:
    """
    Quick function to validate a single content piece

    Args:
        content: GeneratedContent to validate

    Returns:
        ValidationResult
    """
    validator = PersonaValidator()
    return validator.validate(content)


if __name__ == "__main__":
    # Demo/testing functionality
    print("Digital Freeman - Persona Voice Validator")
    print("=" * 50)

    try:
        validator = PersonaValidator()
        print(f"✓ Validator initialized")
        print(f"✓ Threshold: {validator.threshold}")
        print(f"✓ Reject generic: {validator.reject_generic}")
        print(f"✓ Reject corporate: {validator.reject_corporate}")
        print()

        # Test cases
        from src.content.ideation import ContentIdea
        from datetime import datetime

        test_cases = [
            # Good Freeman content
            {
                'text': "Everyone's talking about AI consciousness. Nobody's asking who benefits from the confusion.",
                'should_pass': True,
                'label': "Good Freeman content"
            },
            # Corporate speak
            {
                'text': "Let's leverage AI to synergize our paradigm and disrupt the market.",
                'should_pass': False,
                'label': "Corporate speak"
            },
            # Generic motivational
            {
                'text': "Believe in yourself! Follow your dreams and never give up! ✨",
                'should_pass': False,
                'label': "Generic motivational"
            },
            # Superficial
            {
                'text': "Amazing vibes today! Stay positive! 💖🙏",
                'should_pass': False,
                'label': "Superficial positivity"
            },
            # Good philosophical
            {
                'text': "The system doesn't fear your anger. It fears your questions. Why?",
                'should_pass': True,
                'label': "Philosophical provocation"
            }
        ]

        print("Testing validation on sample content:")
        print("-" * 50)

        for i, test in enumerate(test_cases, 1):
            # Create mock content
            idea = ContentIdea(
                topic="Test Topic",
                source="test",
                category="priority",
                angle="Test angle",
                tone="philosophical",
                generated_at=datetime.now()
            )

            content = GeneratedContent(
                text=test['text'],
                idea=idea,
                platform='twitter',
                character_count=len(test['text']),
                generated_at=datetime.now(),
                llm_provider='test'
            )

            result = validator.validate(content)

            status = "✓ PASS" if result.passed else "✗ FAIL"
            expected = "✓" if test['should_pass'] == result.passed else "✗ MISMATCH"

            print(f"\n{i}. {test['label']} {expected}")
            print(f"   Text: \"{test['text']}\"")
            print(f"   Result: {status} (score: {result.score:.2f})")
            print(f"   Checks: {sum(result.checks.values())}/{len(result.checks)} passed")
            if result.feedback:
                print(f"   Feedback: {result.feedback[0]}")

        print("\n" + "=" * 50)
        print("✓ Validator module working correctly")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
