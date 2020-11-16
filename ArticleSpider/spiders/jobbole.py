# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy.http import Request
from urllib import parse
import json

from ArticleSpider.items import JobboleArticleItem
from ArticleSpider.utils import common


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    def parse(self, response):
        post_nodes = response.xpath('//div[@class="news_block"]')[:1]
        for post_node in post_nodes:
            img_url = post_node.xpath('div[@class="content"]/div[@class="entry_summary"]/a/img/@src').extract_first('')
            if img_url.startswith("//"):
                img_url = "https" + img_url
            post_url = parse.urljoin(response.url, post_node.xpath('div[@class="content"]/h2[@class="news_entry"]/a/@href').extract_first(''))
            yield Request(url=post_url, meta={"front_img_url": img_url}, callback=self.parse_detail)

    def parse_detail(self, response):
        match_re = re.match(".*?(\d+)", response.url)

        if match_re:
            article_item = JobboleArticleItem()

            title = response.xpath('//div[@id="news_title"]/a/text()').extract_first("")
            create_time = response.xpath('//div[@id="news_info"]/span[@class="time"]/text()').extract_first("")
            content = response.xpath('//div[@id="news_body"]').extract()[0]
            tags = ",".join(response.xpath('//div[@id="news_more_info"]/div[@class="news_tags"]/a/text()').extract())

            post_id = match_re.group(1)
            info_url = parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id))

            article_item["title"] = title
            article_item["create_date"] = create_time
            article_item["content"] = content
            article_item["tags"] = tags
            article_item["url"] = response.url
            article_item["url_object_id"] = common.get_md5(response.url)
            article_item["front_img_url"] = [response.meta.get("front_img_url", "")]

            yield Request(url=info_url, meta={"article_item": article_item, "url": response.url}, callback=self.parse_num)

    def parse_num(self, response):
        article_item = response.meta.get("article_item", "")
        j_data = json.loads(response.text)

        praise_nums = j_data["DiggCount"]
        fav_nums = j_data["TotalView"]
        comment_nums = j_data["CommentCount"]

        article_item["praise_nums"] = praise_nums
        article_item["fav_nums"] = fav_nums
        article_item["comment_nums"] = comment_nums

        yield article_item

