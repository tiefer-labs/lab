<picture>
  <source media="(prefers-color-scheme: dark)" srcset="profile/tiefer-logo-white.svg">
  <img alt="Tiefer" src="profile/tiefer-logo.svg" width="200">
</picture>

# Acceptable use policy

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

What Tiefer's products and services may not be used for, how Tiefer applies these limits, and the design commitments that support them. This is a plain-language summary; the binding terms are part of Tiefer's customer agreements.

---

## 1. Scope

| Covered | Not covered |
| :--- | :--- |
| Tiefer's software, models, model updates, alerts and data products delivered to customers and partners | the open-source code in the public repositories, which anyone may use under its licence (section 5) |
| Services Tiefer provides, such as pilots, integration and support | third-party data, models and tools that Tiefer does not provide |

Tiefer builds AI software that runs on Earth observation satellites and at their ground stations. Information from space can affect people's safety and rights, so Tiefer sets clear limits on how its products and services may be used.

---

## 2. Prohibited uses

Tiefer's products and services may not be used to:

1. track, identify, locate or profile individual people;
2. plan or support violence, persecution, or violations of human rights or international humanitarian law;
3. violate sanctions, export control laws or any other applicable law;
4. select targets for an attack, including on critical infrastructure;
5. harass, stalk or intimidate anyone;
6. mislead others by presenting a model's inferences as confirmed observations, or by presenting generated imagery as evidence.

---

## 3. How Tiefer applies this policy

| Measure | What it means |
| :--- | :--- |
| Customer screening | customers and end users are checked against applicable sanctions lists and export control rules before any agreement |
| Purpose statement | each agreement states the intended use; a material change of use needs Tiefer's agreement |
| Public authorities | work for public authorities is done only under the laws of the country concerned and for a clear, lawful purpose |
| Audit trail | model versions, updates and alerts are logged for each deployment |
| Suspension | Tiefer may stop supporting or updating a deployment that breaks this policy, and may end the agreement |

---

## 4. Design commitments

Tiefer designs its products to the following requirements. Each product's documentation states how far each one is implemented and how it is verified.

- Nothing is deleted blindly: frames filtered on board are compressed and kept, and the operator sets the rules.
- Every alert labels what the sensor observed separately from what a model inferred, with a confidence value.
- Generated imagery is never sent as evidence.
- Every model update is signed, versioned and can be rolled back.
- Alerts support human decisions; they do not replace them.

---

## 5. Open-source code

The code in Tiefer's public repositories is licensed under the Mozilla Public License 2.0, and that licence does not restrict how the code may be used. This policy does not change the licence. Tiefer asks everyone who uses its open-source code to respect the same limits, and does not provide support, models or services for uses that break them.

---

## 6. Reporting misuse

If you believe a Tiefer product or service is being misused, write to [hello@tiefer.space](mailto:hello@tiefer.space) with the subject line "Acceptable use". Reports are handled confidentially, and Tiefer confirms receipt within 3 working days (Monday to Friday, Baku time, UTC+4).

---

## 7. Review

This policy is reviewed at least once a year, and whenever the product, Tiefer's customers or the applicable law change in a way that affects it. Every change is listed in the changelog.

---

## Changelog

- 7 October 2026: rewritten to the Tiefer Markdown standard; scope, international humanitarian law, target selection, purpose statement, the relation to the open-source licence, a reporting time and the review cycle added; the product rules are stated as design commitments whose implementation each product documents.
- 27 September 2026: first version.
