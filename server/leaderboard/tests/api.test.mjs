import { protocolSuite } from './protocol-suite.mjs';
import { accountsSuite } from './accounts-suite.mjs';
import { startFixture } from './local-server.mjs';

protocolSuite(startFixture);
accountsSuite(startFixture);
