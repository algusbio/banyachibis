#!/usr/bin/env python3
"""Build a dependency-free static site and insert verified contact/SEO settings."""
import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, urlencode
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Сборка сайта Баня Чибис")
parser.add_argument('--url', help='Полный URL, включая путь репозитория GitHub Pages')
parser.add_argument('--output', default='dist', help='Папка результата; . для обновления корня')
args = parser.parse_args()
settings = json.loads((ROOT / 'settings.json').read_text(encoding='utf-8'))
base = (args.url if args.url is not None else settings.get('site_url', '')).strip()
if base:
    parsed = urlparse(base)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment or parsed.username:
        raise SystemExit('site_url должен быть полным HTTPS URL без параметров и фрагмента')
    base = base.rstrip('/') + '/'
phone = settings.get('phone', '').strip()
if phone and not re.fullmatch(r'\+7\d{10}', phone):
    raise SystemExit('phone: укажите российский номер в формате +7 и 10 цифр без пробелов')
display = settings.get('phone_display', '').strip() or phone
address = settings.get('exact_address', '').strip()
map_url = settings.get('map_url', '').strip()
if map_url and (urlparse(map_url).scheme != 'https' or not urlparse(map_url).netloc):
    raise SystemExit('map_url должен начинаться с https://')
latitude, longitude = settings.get('map_latitude'), settings.get('map_longitude')
if latitude is not None or longitude is not None:
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)) or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise SystemExit('Укажите корректные map_latitude и map_longitude')
output = (ROOT / args.output).resolve()
if output != ROOT and (output == ROOT.parent or ROOT in output.parents and output.name in ('assets', 'scripts')):
    raise SystemExit('Выберите отдельную папку результата, например dist')
output.mkdir(parents=True, exist_ok=True)
page = (ROOT / 'index.html').read_text(encoding='utf-8')

def block(name, content):
    global page
    pattern = rf'<!-- {name}-START -->.*?<!-- {name}-END -->'
    page, count = re.subn(pattern, lambda _: f'<!-- {name}-START -->{content}<!-- {name}-END -->', page, flags=re.S)
    if count != 1:
        raise SystemExit(f'Не найден уникальный блок {name}')

data = [
    (7, 'outside', 'Бревенчатый сруб', 'Баня Чибис: деревянный сруб с крытой верандой среди деревьев'),
    (3, 'steam', 'Парная на дровах', 'Деревянные полки и дровяная печь в парной бани Чибис'),
    (9, 'inside', 'Комната отдыха', 'Комната отдыха со столом и скамейками в бревенчатом срубе'),
    (8, 'outside', 'Крытая веранда', 'Крытая веранда бани Чибис и деревянная дорожка'),
    (1, 'outside', 'Место для посиделок', 'Беседка со столом и скамейками на территории бани'),
    (16, 'outside', 'Природа рядом', 'Вид на воду, деревья и деревянную лестницу на территории'),
    (2, 'steam', 'Тепло парной', 'Парная с деревянными полками и дверью'),
    (4, 'outside', 'Мангальная зона', 'Мангал и беседка рядом с деревянной баней'),
    (5, 'inside', 'Банные принадлежности', 'Полка с банными принадлежностями в помещении бани'),
    (6, 'steam', 'Печь и камни', 'Дровяная печь с камнями и деревянные полки парной'),
    (10, 'inside', 'Санузел', 'Санузел с раковиной внутри бревенчатой бани'),
    (11, 'inside', 'Внутри сруба', 'Входная зона бани Чибис с деревянными стенами'),
    (12, 'steam', 'Ещё один взгляд на парную', 'Широкие полки парной и печь в бане Чибис'),
    (13, 'outside', 'Среди деревьев', 'Зелёная территория и деревянные строения бани Чибис'),
    (14, 'outside', 'Дорожка к природе', 'Деревянная лестница среди зелёных деревьев'),
    (15, 'inside', 'Детали бани', 'Внутреннее помещение бани и вход в парную'),
]
gallery = []
for index, (number, category, caption, alt) in enumerate(data):
    extra = ' photo-extra' if index >= 6 else ''
    width, height = (960, 1280) if number in (14, 16) else (1280, 960)
    small_width = 480 if number in (14, 16) else 640
    gallery.append(f'''<a class="photo{extra}" href="assets/photos/{number:02}.webp" data-category="{category}" data-caption="{html.escape(caption, quote=True)}" aria-label="Увеличить фото: {html.escape(caption, quote=True)}"><img src="assets/photos/{number:02}-small.webp" srcset="assets/photos/{number:02}-small.webp {small_width}w, assets/photos/{number:02}.webp {width}w" sizes="(max-width:560px) 46vw, (max-width:800px) 47vw, 31vw" width="{width}" height="{height}" loading="lazy" decoding="async" alt="{html.escape(alt, quote=True)}"><span class="photo-caption">{caption}<span aria-hidden="true">↗</span></span></a>''')
block('GALLERY', '\n' + '\n'.join(gallery) + '\n')

contact = ''
mobile = '<a href="#price">Стоимость и условия ↗</a>'
if phone:
    contact = f'<a class="contact-phone" href="tel:{phone}">{html.escape(display)}</a><p class="contact-phone-note">Звоните: сообщения могут приходить с задержкой.</p>'
    mobile = f'<a href="tel:{phone}">Позвонить и записаться ↗</a>'
block('CONTACT', contact)
block('MOBILE', mobile)
block('ADDRESS', html.escape(address) if address else 'Республика Татарстан, Высокогорский район,<br>Семиозерское сельское поселение')
if map_url:
    page = re.sub(r'(<a class="map-link" href=")[^"]*(")', lambda m: m[1] + html.escape(map_url, quote=True) + m[2], page)
    page = page.replace('Найти Макаровку на карте', 'Открыть на карте')

if latitude is not None:
    point = f'{longitude},{latitude}'
    widget = 'https://yandex.ru/map-widget/v1/?' + urlencode({'ll': point, 'z': 17, 'pt': point + ',pm2gnm', 'lang': 'ru_RU'})
    route = 'https://yandex.ru/maps/?' + urlencode({'rtext': f'~{latitude},{longitude}', 'rtt': 'auto'})
else:
    widget = 'https://yandex.ru/map-widget/v1/?' + urlencode({'mode': 'search', 'text': address or 'деревня Макаровка, Высокогорский район, Татарстан', 'lang': 'ru_RU'})
    route = map_url or 'https://yandex.ru/maps/'
block('MAP', f'''<div class="map-section" aria-labelledby="map-title">
        <div class="map-heading"><div><h3 id="map-title">Как нас найти</h3><p>Деревня Макаровка, ул. Березовая, д. 9а</p></div><a class="button button-outline" href="{html.escape(route, quote=True)}" target="_blank" rel="noopener noreferrer">Построить маршрут <span aria-hidden="true">↗</span></a></div>
        <div class="map-frame"><iframe src="{html.escape(widget, quote=True)}" title="Яндекс Карта — Баня Чибис, деревня Макаровка, Березовая улица, 9а" width="1200" height="440" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe></div>
        <p class="map-caption">Метка у дома 9а на Березовой улице. <a href="{html.escape(map_url or route, quote=True)}" target="_blank" rel="noopener noreferrer">Открыть адрес в Яндекс Картах ↗</a></p>
      </div>''')

seo = ''
if base:
    safe = html.escape(base, quote=True)
    seo = f'''\n  <link rel="canonical" href="{safe}">
  <meta property="og:url" content="{safe}">
  <meta property="og:image" content="{safe}assets/social.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Деревянная баня Чибис среди деревьев в Макаровке">
  <meta name="twitter:image" content="{safe}assets/social.jpg">\n  '''
block('SEO-URL', seo)
business = {
    '@context': 'https://schema.org', '@type': 'LocalBusiness', 'name': 'Баня Чибис',
    'description': 'Баня на берёзовых дровах в Макаровке рядом с Казанью. Аренда целиком для компании до 6 человек.',
    'address': {'@type': 'PostalAddress', 'addressCountry': 'RU', 'addressRegion': 'Республика Татарстан', 'addressLocality': 'деревня Макаровка, Семиозерское сельское поселение, Высокогорский район'},
    'priceRange': '6 000 ₽ за 3 часа',
    'openingHoursSpecification': {'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 'opens': '00:00', 'closes': '23:59'},
    'makesOffer': {'@type': 'Offer', 'price': '6000', 'priceCurrency': 'RUB', 'itemOffered': {'@type': 'Service', 'name': 'Аренда бани целиком на 3 часа', 'description': 'Для компании до 6 человек. Парная, комната отдыха, мангальная зона и дубовый веник в подарок.'}}
}
if address: business['address']['streetAddress'] = address
if phone: business['telephone'] = phone
if base: business.update({'url': base, 'image': base + 'assets/social.jpg', '@id': base + '#business'})
if map_url: business['hasMap'] = map_url
if latitude is not None:
    business['geo'] = {'@type': 'GeoCoordinates', 'latitude': latitude, 'longitude': longitude}
faq_items = []
def plain(text):
    return html.unescape(re.sub(r'<[^>]+>', '', text)).strip()
for question, answer in re.findall(r'<details><summary>(.*?)<span aria-hidden="true">\+</span></summary><div><p>(.*?)</p></div></details>', page, re.S):
    faq_items.append({'@type': 'Question', 'name': plain(question), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(answer)}})
schema = [business, {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': faq_items}]
block('SCHEMA', '\n  <script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n  ')
(output / 'index.html').write_text(page, encoding='utf-8')
if output != ROOT:
    shutil.copytree(ROOT / 'assets', output / 'assets', dirs_exist_ok=True)
not_found = (ROOT / '404.html').read_text(encoding='utf-8')
not_found = re.sub(r'const basePath=.*?;', 'const basePath=' + json.dumps(urlparse(base).path if base else '') + ';', not_found, count=1)
(output / '404.html').write_text(not_found, encoding='utf-8')
(output / '.nojekyll').write_text('', encoding='utf-8')
robots = 'User-agent: *\nAllow: /\n'
if base:
    robots += f'\nSitemap: {base}sitemap.xml\n'
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{escape(base)}</loc></url></urlset>\n'
    (output / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
elif (output / 'sitemap.xml').exists():
    (output / 'sitemap.xml').unlink()
(output / 'robots.txt').write_text(robots, encoding='utf-8')
print('Готово:', output)
if not phone: print('Телефон не задан: добавьте его в settings.json перед публикацией.')
if not base: print('URL не задан: canonical, og:image и sitemap будут созданы при сборке с --url или через GitHub Actions.')
