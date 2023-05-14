import re
import scrapy
from scrapy.http import Response
from typing import Generator, Any
import config


class VacanciesSpider(scrapy.Spider):
    name = "vacancies"
    allowed_domains = ["djinni.co"]
    start_urls = ["https://djinni.co/jobs/?primary_keyword=Python"]

    def parse(self, response: Response, **kwargs) -> Generator:
        vacancies_links = response.css("a.profile::attr(href)").getall()
        yield from response.follow_all(
            vacancies_links, callback=self.parse_vacancy
        )

        next_page = response.css(
            "li.page-item.active ~ li.page-item a.page-link::attr(href)"
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    @staticmethod
    def parse_vacancy(
        response: Response,
    ) -> Generator[dict[str, list], Any, None]:
        tech_words = config.technologies
        requirements = "".join(
            response.css("div.profile-page-section").getall()
        ).lower()

        tech_dict = {tech.lower(): tech for tech in tech_words}

        technologies = set()
        for span in response.css(
            "div.job-additional-info--item-text span:not(.location-text)[class='']::text"
        ).getall():
            tech = span.strip().lower()
            if tech in tech_dict:
                technologies.add(tech_dict[tech])
            else:
                # check if the technology contains only English letters
                if re.match(r"^[a-zA-Z]+$", tech):
                    # check if the technology does not contain "Developer"
                    if "developer" not in tech:
                        technologies.add(tech.title())

        for tech in tech_words:
            if tech.lower() in requirements and tech not in technologies:
                technologies.add(tech)

        location_text = response.css(".location-text::text").get()
        locations = [
            loc.strip()
            for loc in location_text.split(",\n")
            if loc.strip() and "Релокейт" not in loc
        ]
        additional_info = "".join(
            response.css("div.job-additional-info--item-text::text").getall()
        ).lower()
        company_type = next(
            (
                comp_type
                for comp_type in config.company_types
                if comp_type.lower() in additional_info
            ),
            "Agency",
        )

        yield {
            "title": response.css("h1::text").get().strip(),
            "company": response.css(".job-details--title::text").get().strip(),
            "company_type": company_type,
            "salary": response.css(".public-salary-item::text").get(),
            "technologies": list(technologies),
            "location": locations,
        }
