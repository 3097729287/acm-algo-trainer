import { writeFile } from 'node:fs/promises';
import { SEQUENCE_CODE } from '../src/pages/algorithm-lab/sequenceCode.js';
import { SEQUENCE_PROBLEMS } from '../src/pages/algorithm-lab/sequenceProblems.js';
import { REFERENCES, OFFICIAL_SAMPLES } from '../tests/sequence-references.mjs';
const data = { lessons: SEQUENCE_CODE, problems: SEQUENCE_PROBLEMS, references: REFERENCES, samples: OFFICIAL_SAMPLES };
if (process.argv[2]) await writeFile(process.argv[2], JSON.stringify(data, null, 2)); else console.log(JSON.stringify(data));
