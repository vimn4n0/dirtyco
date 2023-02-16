from .charsetprober import CharSetProber
from .enums import ProbingState



class HebrewProber(CharSetProber):
    # windows-1255 / ISO-8859-8 code points of interest
    FINAL_KAF = 0xea
    NORMAL_KAF = 0xeb
    FINAL_MEM = 0xed
    NORMAL_MEM = 0xee
    FINAL_NUN = 0xef
    NORMAL_NUN = 0xf0
    FINAL_PE = 0xf3
    NORMAL_PE = 0xf4
    FINAL_TSADI = 0xf5
    NORMAL_TSADI = 0xf6

    # Minimum Visual vs Logical final letter score difference.
    # If the difference is below this, don't rely solely on the final letter score
    # distance.
    MIN_FINAL_CHAR_DISTANCE = 5

    # Minimum Visual vs Logical model score difference.
    # If the difference is below this, don't rely at all on the model score
    # distance.
    MIN_MODEL_DISTANCE = 0.01

    VISUAL_HEBREW_NAME = "ISO-8859-8"
    LOGICAL_HEBREW_NAME = "windows-1255"

    def __init__(self):
        super(HebrewProber, self).__init__()
        self._final_char_logical_score = None
        self._final_char_visual_score = None
        self._prev = None
        self._before_prev = None
        self._logical_prober = None
        self._visual_prober = None
        self.reset()

    def reset(self):
        self._final_char_logical_score = 0
        self._final_char_visual_score = 0
        # The two last characters seen in the previous buffer,
        # mPrev and mBeforePrev are initialized to space in order to simulate
        # a word delimiter at the beginning of the data
        self._prev = ' '
        self._before_prev = ' '
        # These probers are owned by the group prober.

    def set_model_probers(self, logicalProber, visualProber):
        self._logical_prober = logicalProber
        self._visual_prober = visualProber

    def is_final(self, c):
        return c in [self.FINAL_KAF, self.FINAL_MEM, self.FINAL_NUN,
                     self.FINAL_PE, self.FINAL_TSADI]

    def is_non_final(self, c):
        # The normal Tsadi is not a good Non-Final letter due to words like
        # 'lechotet' (to chat) containing an apostrophe after the tsadi. This
        # apostrophe is converted to a space in FilterWithoutEnglishLetters
        # causing the Non-Final tsadi to appear at an end of a word even
        # though this is not the case in the original text.
        # The letters Pe and Kaf rarely display a related behavior of not being
        # a good Non-Final letter. Words like 'Pop', 'Winamp' and 'Mubarak'
        # for example legally end with a Non-Final Pe or Kaf. However, the
        # benefit of these letters as Non-Final letters outweighs the damage
        # since these words are quite rare.
        return c in [self.NORMAL_KAF, self.NORMAL_MEM,
                     self.NORMAL_NUN, self.NORMAL_PE]

    def feed(self, byte_str):
        # Final letter analysis for logical-visual decision.
        # Look for evidence that the received buffer is either logical Hebrew
        # or visual Hebrew.
        # The following cases are checked:
        # 1) A word longer than 1 letter, ending with a final letter. This is
        #    an indication that the text is laid out "naturally" since the
        #    final letter really appears at the end. +1 for logical score.
        # 2) A word longer than 1 letter, ending with a Non-Final letter. In
        #    normal Hebrew, words ending with Kaf, Mem, Nun, Pe or Tsadi,
        #    should not end with the Non-Final form of that letter. Exceptions
        #    to this rule are mentioned above in isNonFinal(). This is an
        #    indication that the text is laid out backwards. +1 for visual
        #    score
        # 3) A word longer than 1 letter, starting with a final letter. Final
        #    letters should not appear at the beginning of a word. This is an
        #    indication that the text is laid out backwards. +1 for visual
        #    score.
        #
        # The visual score and logical score are accumulated throughout the
        # text and are finally checked against each other in GetCharSetName().
        # No checking for final letters in the middle of words is done since
        # that case is not an indication for either Logical or Visual text.
        #
        # We automatically filter out all 7-bit characters (replace them with
        # spaces) so the word boundary detection works properly. [MAP]

        if self.state == ProbingState.NOT_ME:
            # Both model probers say it's not them. No reason to continue.
            return ProbingState.NOT_ME

        byte_str = self.filter_high_byte_only(byte_str)

        for cur in byte_str:
            if cur == ' ':
                # We stand on a space - a word just ended
                if self._before_prev != ' ':
                    # next-to-last char was not a space so self._prev is not a
                    # 1 letter word
                    if self.is_final(self._prev):
                        # case (1) [-2:not space][-1:final letter][cur:space]
                        self._final_char_logical_score += 1
                    elif self.is_non_final(self._prev):
                        # case (2) [-2:not space][-1:Non-Final letter][
                        #  cur:space]
                        self._final_char_visual_score += 1
            else:
                # Not standing on a space
                if ((self._before_prev == ' ') and
                        (self.is_final(self._prev)) and (cur != ' ')):
                    # case (3) [-2:space][-1:final letter][cur:not space]
                    self._final_char_visual_score += 1
            self._before_prev = self._prev
            self._prev = cur

        # Forever detecting, till the end or until both model probers return
        # ProbingState.NOT_ME (handled above)
        return ProbingState.DETECTING

    @property
    def charset_name(self):
        # Make the decision: is it Logical or Visual?
        # If the final letter score distance is dominant enough, rely on it.
        finalsub = self._final_char_logical_score - self._final_char_visual_score
        if finalsub >= self.MIN_FINAL_CHAR_DISTANCE:
            return self.LOGICAL_HEBREW_NAME
        if finalsub <= -self.MIN_FINAL_CHAR_DISTANCE:
            return self.VISUAL_HEBREW_NAME

        # It's not dominant enough, try to rely on the model scores instead.
        modelsub = (self._logical_prober.get_confidence()
                    - self._visual_prober.get_confidence())
        if modelsub > self.MIN_MODEL_DISTANCE:
            return self.LOGICAL_HEBREW_NAME
        if modelsub < -self.MIN_MODEL_DISTANCE:
            return self.VISUAL_HEBREW_NAME

        # Still no good, back to final letter distance, maybe it'll save the
        # day.
        if finalsub < 0.0:
            return self.VISUAL_HEBREW_NAME

        # (finalsub > 0 - Logical) or (don't know what to do) default to
        # Logical.
        return self.LOGICAL_HEBREW_NAME

    @property
    def language(self):
        return 'Hebrew'

    @property
    def state(self):
        # Remain active as long as any of the model probers are active.
        if (self._logical_prober.state == ProbingState.NOT_ME) and \
           (self._visual_prober.state == ProbingState.NOT_ME):
            return ProbingState.NOT_ME
        return ProbingState.DETECTING
