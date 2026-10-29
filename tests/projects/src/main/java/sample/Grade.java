package sample;

/** A deliberately part-tested class, so Pitest leaves some mutants alive. */
public final class Grade {
    private Grade() {
    }

    public static String of(int score) {
        if (score >= 80) {
            return "A";
        }
        if (score >= 60) {
            return "B";
        }
        return "C";
    }

    public static int clamp(int value) {
        return Math.max(0, Math.min(100, value));
    }
}
