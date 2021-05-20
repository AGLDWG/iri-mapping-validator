import json
import httpx
import asyncio
import argparse
from argparse import RawTextHelpFormatter
from prettytable import PrettyTable
import textwrap
from operator import attrgetter


class ValidationResult:
    def __init__(self, label: str, success: bool, message: str, from_iri: str, expected_result: str, actual_result: str, request_headers: dict):
        self.label = label
        self.success = success
        self.message = message
        self.from_iri = from_iri
        self.expected_result = expected_result
        self.actual_result = actual_result
        self.request_headers = request_headers


def validate_redirect(label: str, from_iri: str, from_headers: dict, to_iri: str) -> ValidationResult:
    """Validates that a redirect works as expected"""
    r = httpx.get(from_iri, headers=from_headers, allow_redirects=False)

    success = r.headers.get("Location") == to_iri
    return ValidationResult(
        label,
        success,
        "" if success else "IRI redirection invalid",
        from_iri,
        to_iri,
        r.headers.get("Location"),
        from_headers
    )


async def get_many(urls, headers=None):
    async def get_async(url):
        try:
            async with httpx.AsyncClient() as client:
                return await client.get(url, headers=headers)
        except Exception as e:
            return httpx.Response(status_code=500)

    resps = await asyncio.gather(*map(get_async, urls))
    return tuple(zip(urls, resps))


def http_failures(urls):
    results = asyncio.run(get_many(urls))
    return [
        (results[0], results[1].status_code)
        for results in results if hasattr(results[1], "is_error") and results[1].is_error]


def http_rdf_failures(urls):
    results = asyncio.run(get_many(urls, headers={"Accept": "text/turtle"}))
    return [
        (results[0], results[1].status_code)
        for results in results if hasattr(results[1], "is_error") and results[1].is_error]


def ld_failures(urls):
    results = asyncio.run(get_many(urls))
    results_rdf = asyncio.run(get_many(urls, headers={"Accept": "text/turtle"}))
    results_all = []
    for r in range(len(results)):
        if hasattr(results[r][1], "is_error") and results[r][1].is_error or \
                hasattr(results_rdf[r][1], "is_error") and results_rdf[r][1].is_error:
            results_all.append((results[r][0], results[r][1], results_rdf[r][1]))

    return results_all


def load_domain(domain_file: str):
    return json.load(open(domain_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        # epilog="""This is \n some, multi-line\n\n eiplog stuff."""
    )

    parser.add_argument(
        "irifiles",
        help="The JSON file(s) containing IRIs to validate redirections from/to. Separate files with commas, no spaces."
    )

    parser.add_argument(
        "-m",
        "--mode",
        help="The mode of validation. 'iri' is default.\n\n"
             "'mappings'\t- validates IRI mappings only, i.e. that the IRIs redirect as indended. Tests must be "
             "supplied by IRI submitters\n"
             "'failures'\t- finds mappings that result in an error code, i.e. anything other than an HTTP 2xx code, "
             "after redirects have been followed\n"
             "'rdf'\t\t- validates that all IRIs result in returned RDF\n"
             "'ld'\t\t- validates that all IRIs result in returned RDF and HTML\n",
        choices=["mappings", "failures", "rdf", "ld"],
        default="mappings",
    )

    args = parser.parse_args()

    files = args.irifiles.split(",")
    d = {}
    for file in files:
        d.update(json.load(open(file)))

    if args.mode == "mappings":  # default
        x = PrettyTable()
        x.field_names = ["Redirect Name", "Expected", "Actual"]

        results = []
        failures = False
        for k, v in d.items():
            for iri in v:
                vr = validate_redirect(iri["label"], iri["from_iri"], iri["from_headers"], iri["to_iri"])
                results.append(vr)
                if not vr.success:
                    failures = True
                    x.add_row([
                        iri["label"],
                        textwrap.fill(iri["to_iri"], 50),
                        textwrap.fill(vr.actual_result, 50)
                    ])
        if failures:
            print("FAILURES")
            x.align = "l"
            print(x)

        print("ALL RESULTS")
        y = PrettyTable()
        y.field_names = ["Redirect Test Name", "Passed"]
        for r in sorted(results, key=attrgetter("success")):
            y.add_row([r.label, r.success])
        y.align = "l"
        print(y)
    elif args.mode == "failures":
        x = PrettyTable()
        x.field_names = ["Passed", "Redirect Test Name"]
        for f in http_failures([x for x in d.keys()]):
            x.add_row([f[0], f[1]])
        x.align = "l"
        print(x)
    elif args.mode == "rdf":
        x = PrettyTable()
        x.field_names = ["Passed", "Redirect Test Name"]
        urls = [x for x in d.keys()]
        failures = False
        failed = []
        for f in http_rdf_failures(urls):
            x.add_row([f[0], f[1]])
            failed.append(f[0])
            failures = True

        if failures:
            print("FAILURES")
            x.align = "l"
            print(x)
        print("WORKING")
        y = PrettyTable()
        y.field_names = ["IRI"]
        y.add_row(["\n".join(sorted(list(set(urls) - set(failed))))])
        y.align = "l"
        print(y)
    elif args.mode == "ld":
        x = PrettyTable()
        x.field_names = ["IRI", "HTML Satus", "RDF Status"]
        r = ld_failures([x for x in d.keys()])
        if len(r) > 0:
            print("FAILURES")
            for f in r:
                x.add_row([f[0], f[1].status_code, f[2].status_code])
            x.align = "l"
            print(x)
        else:
            print("no failures")
