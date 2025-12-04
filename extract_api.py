"""
Извлечение API endpoints из минифицированного JavaScript
"""

import re

# Читаем JavaScript файл
with open('main_app.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

print("=== ИЗВЛЕЧЕНИЕ API ENDPOINTS ===\n")

# Ищем все строки с /api/
api_pattern = r'["\'](/api/[^"\']+)["\']'
api_matches = re.findall(api_pattern, js_content)

print(f"Найдено {len(api_matches)} упоминаний API endpoints:\n")

# Убираем дубликаты и сортируем
unique_apis = sorted(set(api_matches))

for api in unique_apis:
    print(f"  {api}")

# Ищем baseURL или apiUrl
print("\n=== ПОИСК BASE URL ===\n")

base_url_patterns = [
    r'baseURL["\s:]+["\']([^"\']+)["\']',
    r'apiUrl["\s:]+["\']([^"\']+)["\']',
    r'apiProdUrl["\s:]+["\']([^"\']+)["\']',
    r'API_URL["\s:]+["\']([^"\']+)["\']',
]

for pattern in base_url_patterns:
    matches = re.findall(pattern, js_content)
    if matches:
        print(f"Найдено по паттерну {pattern}:")
        for match in set(matches):
            print(f"  {match}")

# Ищем axios.create или похожие конфигурации
print("\n=== ПОИСК AXIOS КОНФИГУРАЦИИ ===\n")

# Ищем контекст вокруг axios
axios_pattern = r'axios\.create\([^)]{0,500}\)'
axios_matches = re.findall(axios_pattern, js_content)

if axios_matches:
    print(f"Найдено {len(axios_matches)} axios.create конфигураций:")
    for i, match in enumerate(axios_matches[:3], 1):
        print(f"\n{i}. {match[:200]}...")

# Ищем все упоминания russiarunning.com
print("\n=== ПОИСК RUSSIARUNNING.COM URLs ===\n")

rr_pattern = r'https?://[^"\s]*russiarunning\.com[^"\s]*'
rr_matches = re.findall(rr_pattern, js_content)

if rr_matches:
    unique_rr = sorted(set(rr_matches))
    for url in unique_rr[:10]:
        print(f"  {url}")

print("\n=== ИЗВЛЕЧЕНИЕ ЗАВЕРШЕНО ===")
