#servjice/nutrition_parse.py
def parse_nutrition_data(data: dict) -> dict:
    result = {}

    try:
        nutrients = data.get("nutrients", [])
        result["calories"] = next((n["amount"] for n in nutrients if n["name"] == "Calories"), None)
        result["protein"] = next((n["amount"] for n in nutrients if n["name"] == "Protein"), None)
        result["fat"] = next((n["amount"] for n in nutrients if n["name"] == "Fat"), None)
        result["carbs"] = next((n["amount"] for n in nutrients if n["name"] == "Carbohydrates"), None)
        result["sugar"] = next((n["amount"] for n in nutrients if n["name"] == "Sugar"), None)
        result["fiber"] = next((n["amount"] for n in nutrients if n["name"] == "Fiber"), None)
    except Exception as e:
        print(f"[ERROR] Failed to parse nutrition data: {e}")

    return result

def parse_nutrition_summary(data: dict, limit=10) -> list[str]:
    """
    Returns a list of formatted strings for the top nutrients.
    """
    lines = []
    try:
        nutrients = data.get("nutrients", [])
        for n in nutrients[:limit]:
            try:
                title = n.get("title", n.get("name", "Unknown"))
                amount = n.get("amount", "?")
                unit = n.get("unit", "")
                daily = n.get("percentOfDailyNeeds", "?")
                lines.append(f"{title}: {amount} {unit} ({daily}% daily)")
            except KeyError as e:
                print(f"[WARN] Skipping nutrient due to missing key: {e}")
    except Exception as e:
        print(f"[ERROR] Failed to summarize nutrition data: {e}")
    return lines
