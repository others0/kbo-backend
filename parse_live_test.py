from bs4 import BeautifulSoup

with open("livetext_dump.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Inning
inning_elem = soup.find(id="lblInning")
print("Inning:", inning_elem.text if inning_elem else "N/A")

# Base info (class="groundBase")
# The bases usually have class "on" if occupied.
# Let's find elements inside .groundBase
ground_base = soup.select_one(".groundBase")
if ground_base:
    # 1B, 2B, 3B are usually span or li
    bases = ground_base.find_all("span")
    for i, b in enumerate(bases):
        print(f"Base {i+1}: class={b.get('class')}")
else:
    print("groundBase not found")

# SBO (Strikes, Balls, Outs)
# Usually inside class="numCon" or similar
sbo = soup.select(".numCon")
if sbo:
    print("SBO html:", sbo[0].prettify()[:500])

# Pitcher / Batter
who = soup.select(".who")
if who:
    print("Who:", who[0].text.strip().replace("\n", " ")[:200])

