plugins {
    java
    id("info.solidsoft.pitest") version "1.19.0"
}

repositories {
    mavenCentral()
}

// shared with the Maven sample
sourceSets {
    main { java.setSrcDirs(listOf("../src/main/java")) }
    test { java.setSrcDirs(listOf("../src/test/java")) }
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.14.4"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}

pitest {
    pitestVersion = "1.30.1"
    junit5PluginVersion = "1.2.3"
    targetClasses = listOf("sample.*")
    outputFormats = listOf("XML", "HTML")
    timestampedReports = false
}
