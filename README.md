# PitestCI

A continuous integration script for processing Pitest output and converting to a summary or GitHub Shield.

Originally a self contained script, made largely obsolete by scripts inside gradle:

```kotlin
/**
 * Substitute for the lack of a Pitest report service
 */
tasks.register("pitestBadge") {
    dependsOn("pitest")

    doLast {
        val mutations = DocumentBuilderFactory.newInstance()
            .newDocumentBuilder()
            .parse(file("build/reports/pitest/mutations.xml"))
            .getElementsByTagName("mutation")

        val statuses = (0 until mutations.length)
            .map { mutations.item(it) }
            .map {
                it.attributes
                    .getNamedItem("status")
                    .nodeValue
            }

        val total = statuses.size
        val killed = statuses.count { it == "KILLED" }

        val score = if (total == 0) 0 else ((killed.toDouble() / total) * 100).roundToInt()

        val color = when {
            score >= 80 -> "brightgreen"
            score >= 60 -> "yellow"
            else -> "red"
        }

        val badgeJson = """
        {
          "schemaVersion": 1,
          "label": "mutation coverage",
          "message": "$score%",
          "color": "$color"
        }
        """.trimIndent()

        val badgesDir = file("badges")
        badgesDir.mkdirs()

        file("badges/pitest.json").writeText(badgeJson)

        println("Mutation coverage: $score%")
    }
}
```

and some custom GitHub actions and GitHub Pages work in gradle.yml

```yml
      - name: Generate PIT badge
        run: ./gradlew pitestBadge

      - name: Upload PIT badge to Pages
        uses: actions/upload-pages-artifact@v4
        with:
          path: badges

      - name: Deploy PIT badge to Pages
        id: deployment
        uses: actions/deploy-pages@v4
```
