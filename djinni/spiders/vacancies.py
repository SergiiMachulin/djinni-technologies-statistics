import re
import scrapy
from scrapy.http import Response
from typing import Generator, Any
import config


DIRECTION = "Python"


class VacanciesSpider(scrapy.Spider):
    name = "vacancies"
    allowed_domains = ["djinni.co"]

    def start_requests(self):
        url = f"https://djinni.co/jobs/?primary_keyword={DIRECTION}"
        experience = getattr(self, "experience", None)
        if experience is not None:
            url += f"&exp_level={experience}"
        yield scrapy.Request(url, self.parse)

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
        vacancy = {}
        vacancy.update(VacanciesSpider.parse_title(response))
        vacancy.update(VacanciesSpider.parse_company(response))
        vacancy.update(VacanciesSpider.parse_company_type(response))
        vacancy.update(VacanciesSpider.parse_salary(response))
        vacancy.update(VacanciesSpider.parse_technologies(response))
        vacancy.update(VacanciesSpider.parse_location(response))

        yield vacancy

    @staticmethod
    def parse_title(response: Response) -> dict[str, str]:
        return {"title": response.css("h1::text").get().strip()}

    @staticmethod
    def parse_company(response: Response) -> dict[str, str]:
        return {
            "company": response.css(".job-details--title::text").get().strip()
        }

    @staticmethod
    def parse_company_type(response: Response) -> dict[str, str]:
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

        return {"company_type": company_type}

    @staticmethod
    def parse_salary(response: Response) -> dict[str, str]:
        return {"salary": response.css(".public-salary-item::text").get()}

    @staticmethod
    def parse_technologies(response: Response) -> dict[str, list]:
        tech_words = config.technologies
        requirements = "".join(
            response.css("div.profile-page-section").getall()
        ).lower()

        tech_dict = {tech.lower(): tech for tech in tech_words}

        technologies = set()
        for span in response.css(
            "div.job-additional-info--item-text "
            "span:not(.location-text)[class='']::text"
        ).getall():
            tech = span.strip().lower()
            if tech in tech_dict:
                technologies.add(tech_dict[tech])
            elif re.match(r"^[a-zA-Z]+$", tech) and "developer" not in tech:
                technologies.add(tech.title())

        for tech in tech_words:
            if tech.lower() in requirements and tech not in technologies:
                technologies.add(tech)

        return {"technologies": list(technologies)}

    @staticmethod
    def parse_location(response: Response) -> dict[str, list]:
        location_text = response.css(".location-text::text").get()
        locations = [
            loc.strip()
            for loc in location_text.split(",\n")
            if loc.strip() and "Релокейт" not in loc
        ]

        return {"location": locations}
