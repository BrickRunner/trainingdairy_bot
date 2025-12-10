from utils.unit_converter import safe_convert_distance_name

result = safe_convert_distance_name("500м плавание + 3000м бег", "мили")
print(f"Result: '{result}'")
print(f"Contains 'ярдов': {'ярдов' in result}")
print(f"Contains 'мили': {'мили' in result}")
print(f"Contains 'ярдоиля': {'ярдоиля' in result}")
