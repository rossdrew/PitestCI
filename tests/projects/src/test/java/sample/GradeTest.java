package sample;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

// of() only far from its boundaries, clamp() not at all
class GradeTest {
    @Test
    void grades() {
        assertEquals("A", Grade.of(95));
        assertEquals("C", Grade.of(10));
    }
}
