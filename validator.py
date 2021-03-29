import json
import httpx


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


def load_domain(domain_file: str):
    return json.load(open(domain_file))


if __name__ == "__main__":
    # d = load_domain("environment.data.gov.au.json")
    # results = []
    # for k, v in d.items():
    #     for iri in v:
    #         results.append(validate_redirect(iri["label"], iri["from_iri"], iri["from_headers"], iri["to_iri"]))

    d = json.load(open("linked.data.gov.au-registers.json"))
    d.update(json.load(open("linked.data.gov.au-ontologies.json")))
    d.update(json.load(open("linked.data.gov.au-vocabs.json")))
    d.update(json.load(open("linked.data.gov.au-datasets.json")))
    d.update(json.load(open("linked.data.gov.au-linksets.json")))
    d.update(json.load(open("linked.data.gov.au-profiles.json")))
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
