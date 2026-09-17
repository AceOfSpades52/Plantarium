#!/data/data/com.termux/files/usr/bin/sh
set -eu
cd "$(dirname "$0")"
echo "Plantarium v0.1.4 — verification"
python -m unittest discover -s tests -v
rm -f plant_medical_demo.sqlite3 plant_research_demo.sqlite3 plant_replay_demo.sqlite3 plant_guided_demo.sqlite3
python -m planticu demo --steps 18 --database plant_medical_demo.sqlite3
python -m planticu replay-demo --database plant_replay_demo.sqlite3
python -m planticu research-demo --database plant_research_demo.sqlite3
python -m planticu guided-demo --database plant_guided_demo.sqlite3
echo "Plantarium v0.1.4 — PASS"
