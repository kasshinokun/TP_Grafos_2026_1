# Main instruction

export PATH="/usr/lib/jvm/java-21-openjdk-amd64/bin:$PATH"
cd /home/claude/graph-tool
mkdir -p out
find src/main/java -name "*.java" | xargs javac -d out --release 21 2>&1
echo "Exit: $?"

# Instruction 1
ls /usr/lib/jvm/java-21-openjdk-amd64/bin/ 2>/dev/null | head -5; find / -name "javac" 2>/dev/null | head -5

# Instruction 2
apt-get install -y default-jdk 2>&1 | tail -5

# Instruction 3
apt-get install -y --fix-missing default-jdk-headless 2>&1 | tail -3; find / -name "javac" 2>/dev/null


# Instruction 4
cd /home/claude/graph-tool && find src -name "*.java" | sort | wc -l && find src -name "*.java" | sort