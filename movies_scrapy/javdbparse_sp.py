from scrapy import Selector
import json
import re


def __parse_score__(score_text):
    score, voters = None, None
    if score_text:
        match = re.search(r'(\d+\.\d+), by (\d+) users', score_text.strip())
        if match:
            score = match.group(1)
            voters = match.group(2)

    return score, voters


def javdb_parser(body: str, source_url):

    rel_urls_xpath = "//article[contains(@class, 'message') and contains(@class, 'video-panel') and .//div[contains(@class, 'message-header')]/p[contains(text(), 'You may also like')]]//div[contains(@class, 'message-body')]//a/@href"
    code_xpath = '//strong[contains(text(), "ID:") or contains(text(), "番號:") ]/following-sibling::a//@data-clipboard-text'
    cover_xpath = '//img[@class="video-cover"]/@src'
    intro_video_xpath = '//video[@id="preview-video"]/source/@src'
    intro_images_xpath = '//div[@class="tile-images preview-images"]//a[@class="tile-item"]/@href'
    release_date_xpath = '//strong[contains(text(),"Released Date:") or contains(text(),"日期:")]/following-sibling::span[@class="value"]/text()'
    duration_xpath = '//strong[contains(text(),"Duration:") or contains(text(),"時長:")]/following-sibling::span[@class="value"]/text()'
    maker_xpath = '//strong[contains(text(),"Maker:") or contains(text(),"片商:")]/following-sibling::span[@class="value"]/a/text()'
    actress_xpath = '//strong[contains(text(), "演員:") or contains(text(), "Actor(s):")]/following-sibling::span[@class="value"]/strong[''@class="symbol female"]/preceding-sibling::a[1]/text()'
    score_xpath = '//strong[contains(text(),"Rating:") or contains(text(),"評分:")]/following-sibling::span[@class="value"]/text()'
    rel_urls_xpath = "//article[contains(@class, 'message') and contains(@class, 'video-panel') and .//div[contains(@class, 'message-header')]/p[contains(text(), 'You may also like')]]//div[contains(@class, 'message-body')]//a/@href"

    selector = Selector(text=body)

    code = selector.xpath(code_xpath).extract_first()
    cover = selector.xpath(cover_xpath).extract_first()
    intro_video = selector.xpath(intro_video_xpath).extract_first()
    intro_images = selector.xpath(intro_images_xpath).extract()
    release_date = selector.xpath(release_date_xpath).extract_first()
    duration = selector.xpath(duration_xpath).extract()
    actress = selector.xpath(actress_xpath).extract()
    maker = selector.xpath(maker_xpath).extract_first()
    rel_urls = selector.xpath(rel_urls_xpath).extract()
    score_text = selector.xpath(score_xpath).extract_first()

    score, voters = __parse_score__(score_text)

    if duration:
        duration = re.search(r'(\d+)', duration[0])
        if duration:
            duration = duration.group()

    items = selector.xpath(
        '//div[@id="magnets-content"]/div[contains(@class,"item columns is-desktop")]')
    links = []
    if items:
        for item in items:
            magnet_link = item.xpath('.//a/@href').extract_first()
            time = item.xpath('.//span[@class="time"]/text()').extract_first()
            size_text = item.xpath(
                './/span[@class="meta"]/text()').extract_first()
            size = ''
            if size_text:
                size_match = re.search(r'(\d+\.\d+GB)', size_text)
                if size_match:
                    size = size_match.group()
            if magnet_link:
                links.append({
                    'magnet_link': magnet_link if magnet_link else '',
                    'upload': time if time else '',
                    'size': size
                })

    media_urls = []
    if cover:
        media_urls.append({'url': cover, 'type': 2})
    if intro_video:
        media_urls.append({'url': intro_video, 'type': 3})
    if intro_images:
        t = [{'url': item, 'type': 1} for item in intro_images]
        media_urls.extend(t)

    media_urls = [item for item in media_urls if item["url"]]


    return {
        'code': code,
        'actress': actress,
        'release_date': release_date,
        'score': score,
        'voters': voters,
        'maker': maker,
        'media_urls': media_urls,
        'duration': duration,
        'links': links,
        'crawl_url': source_url,
        'rel_urls': rel_urls
    }


if __name__ == '__main__':
    with open('/Users/fengpan/Downloads/ss4/_v_kABEY.html', 'r') as f:
        content = f.read()
    item = javdb_parser(content)

    with open('temp_v2.json', 'w') as f:
        json.dump(item, f, indent=2)
