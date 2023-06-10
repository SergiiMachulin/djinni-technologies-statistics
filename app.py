import subprocess
import time

output_files = [
    "vacancies_all.jl",
    "vacancies_junior.jl",
    "vacancies_junior.jl",
    "vacancies_middle.jl",
    "vacancies_senior.jl",
]

experiences = [
    None,
    "no_exp",
    "1y",
    "3y",
    "5y",
]


def run_scrapy_command(output_file, experience):
    command = ["scrapy", "crawl", "vacancies", "-o", output_file]
    if experience:
        command += ["-a", f"experience={experience}"]
    subprocess.run(command)


if __name__ == "__main__":
    start_time = time.time()

    for output_file, experience in zip(output_files, experiences):
        run_scrapy_command(output_file, experience)

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    print("All vacancies have been scraped successfully.")
    print(f"Execution time: {execution_time} seconds.")
