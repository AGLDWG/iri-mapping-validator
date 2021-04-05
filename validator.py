import json
import httpx
import asyncio
import argparse
from argparse import RawTextHelpFormatter


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
            print(url)
            print(e)

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
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, epilog="""This is \n some, multi-line\n\n eiplog stuff.""")
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

    d = json.load(open("linked.data.gov.au-registers.json"))
    d.update(json.load(open("linked.data.gov.au-ontologies.json")))
    d.update(json.load(open("linked.data.gov.au-vocabs.json")))
    d.update(json.load(open("linked.data.gov.au-datasets.json")))
    d.update(json.load(open("linked.data.gov.au-linksets.json")))
    d.update(json.load(open("linked.data.gov.au-profiles.json")))

    if args.mode == "mappings":  # default
        results = []
        print("FAILURES")
        no_failures = True
        for k, v in d.items():
            for iri in v:
                vr = validate_redirect(iri["label"], iri["from_iri"], iri["from_headers"], iri["to_iri"])
                results.append(vr)
                if not vr.success:
                    no_failures = False
                    print("for \"{}\", to: {}, got: {}".format(iri["label"], iri["to_iri"], vr.actual_result))
        if no_failures:
            print("none")
        print()
        print("ALL RESULTS")
        for r in results:
            print(r.success, r.label)
    elif args.mode == "failures":
        print("FAILURES")
        for f in http_failures([x for x in d.keys()]):
            print(f[0], f[1])
    elif args.mode == "rdf":
        print("FAILURES")
        for f in http_failures([x for x in d.keys()]):
            print(f[0], f[1])
    elif args.mode == "ld":
        print("FAILURES")
        for f in ld_failures([x for x in d.keys()]):
            print(f[0], f[1].status_code, f[2].status_code)
