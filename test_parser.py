"""
Тестовый скрипт для изучения структуры сайта reg.russiarunning.com
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def explore_site():
    """Исследовать структуру сайта"""
    url = "https://reg.russiarunning.com/"

    async with aiohttp.ClientSession() as session:
        try:
            print(f"Загружаю страницу: {url}")
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()

                    # Сохраняем HTML в файл для анализа
                    with open("site_structure.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print("HTML сохранен в site_structure.html")

                    # Парсим структуру
                    soup = BeautifulSoup(html, 'lxml')

                    print("\n=== АНАЛИЗ СТРУКТУРЫ САЙТА ===\n")

                    # Ищем все select элементы (выпадающие списки)
                    print("--- ВЫПАДАЮЩИЕ СПИСКИ (select) ---")
                    selects = soup.find_all('select')
                    for i, select in enumerate(selects, 1):
                        select_id = select.get('id', 'Нет ID')
                        select_name = select.get('name', 'Нет name')
                        select_class = select.get('class', 'Нет class')
                        print(f"\nSelect #{i}:")
                        print(f"  ID: {select_id}")
                        print(f"  Name: {select_name}")
                        print(f"  Class: {select_class}")

                        options = select.find_all('option')
                        print(f"  Количество options: {len(options)}")
                        if options and len(options) <= 10:
                            print("  Options:")
                            for opt in options[:10]:
                                value = opt.get('value', '')
                                text = opt.text.strip()
                                print(f"    - value='{value}' text='{text}'")

                    # Ищем формы
                    print("\n--- ФОРМЫ (form) ---")
                    forms = soup.find_all('form')
                    for i, form in enumerate(forms, 1):
                        form_id = form.get('id', 'Нет ID')
                        form_action = form.get('action', 'Нет action')
                        form_method = form.get('method', 'GET')
                        print(f"\nForm #{i}:")
                        print(f"  ID: {form_id}")
                        print(f"  Action: {form_action}")
                        print(f"  Method: {form_method}")

                    # Ищем списки соревнований
                    print("\n--- ПОИСК СПИСКА СОРЕВНОВАНИЙ ---")

                    # Пробуем разные варианты
                    possible_containers = [
                        soup.find_all('div', class_=lambda x: x and 'event' in x.lower()),
                        soup.find_all('div', class_=lambda x: x and 'competition' in x.lower()),
                        soup.find_all('div', class_=lambda x: x and 'race' in x.lower()),
                        soup.find_all('article'),
                        soup.find_all('div', class_=lambda x: x and 'item' in x.lower()),
                    ]

                    for i, containers in enumerate(possible_containers):
                        if containers:
                            print(f"\nНайден вариант #{i+1}: {len(containers)} элементов")
                            if containers:
                                first = containers[0]
                                print(f"Пример первого элемента:")
                                print(f"  Tag: {first.name}")
                                print(f"  Classes: {first.get('class', [])}")
                                print(f"  Первые 200 символов: {str(first)[:200]}...")

                    # Ищем ссылки на соревнования
                    print("\n--- ССЫЛКИ (a href) ---")
                    links = soup.find_all('a', href=True)
                    competition_links = [
                        link for link in links
                        if 'event' in link.get('href', '').lower()
                        or 'race' in link.get('href', '').lower()
                        or 'competition' in link.get('href', '').lower()
                    ]
                    print(f"Найдено потенциальных ссылок на соревнования: {len(competition_links)}")
                    for link in competition_links[:5]:
                        print(f"  - {link.get('href')} : {link.text.strip()[:50]}")

                    # Ищем все уникальные классы
                    print("\n--- ТОП-20 САМЫХ ЧАСТЫХ КЛАССОВ ---")
                    all_classes = {}
                    for tag in soup.find_all(class_=True):
                        classes = tag.get('class', [])
                        for cls in classes:
                            all_classes[cls] = all_classes.get(cls, 0) + 1

                    sorted_classes = sorted(all_classes.items(), key=lambda x: x[1], reverse=True)
                    for cls, count in sorted_classes[:20]:
                        print(f"  .{cls} : {count} раз")

                    # Ищем JavaScript переменные с данными
                    print("\n--- JAVASCRIPT ПЕРЕМЕННЫЕ ---")
                    scripts = soup.find_all('script')
                    for script in scripts:
                        script_text = script.string
                        if script_text and ('var' in script_text or 'const' in script_text or 'let' in script_text):
                            if 'event' in script_text.lower() or 'competition' in script_text.lower():
                                print(f"Найден скрипт с данными:")
                                print(script_text[:300])
                                print("...")
                                break

                    print("\n=== АНАЛИЗ ЗАВЕРШЕН ===")
                    print("Подробный HTML сохранен в файл site_structure.html")

                else:
                    print(f"Ошибка: статус {response.status}")

        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(explore_site())
