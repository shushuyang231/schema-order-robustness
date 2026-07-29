# License and redistribution boundaries

This file describes the intended submission artifact. It is not legal advice.

## Project-created material

- Project source code and test code are released under the MIT License in
  `LICENSE`.
- The manuscript, submission PDF, project-created figures, and project-created
  tables are prepared for TMLR under CC BY 4.0, as required by TMLR from the
  time of submission.
- Synthetic examples in `data/public/` may be redistributed with the project
  code.

## Third-party material

- The TMLR style files are copied unmodified from
  <https://github.com/JmlrOrg/tmlr-style-file> and retain their upstream
  Apache-2.0 license and notices.
- The Structured Output Benchmark (SOB) code is distributed upstream under
  MIT. Its README states that source datasets retain their original licenses,
  including HotpotQA under CC BY-SA 4.0. The anonymous artifact therefore does
  not redistribute the downloaded SOB parquet file or frozen benchmark
  contexts.
- BIRD-Critic material belongs to an abandoned early project direction and is
  excluded from the paper artifact.

## Material retained locally but excluded from the anonymous artifact

- API credentials and `.env` files.
- Restricted gold-answer files.
- Raw provider responses, reasoning content, and smoke-response content.
- Downloaded benchmark parquet files and benchmark contexts.
- Third-party vendor repositories.

The artifact includes aggregate result reports, code, protocols, tests, and
cryptographic hashes needed to audit paper claims without silently granting
redistribution rights over excluded material.
