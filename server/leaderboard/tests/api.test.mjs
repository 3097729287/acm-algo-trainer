import { protocolSuite } from './protocol-suite.mjs';
import { accountsSuite } from './accounts-suite.mjs';
import { startFixture } from './local-server.mjs';
import { socialSuite } from './social-suite.mjs';

protocolSuite(startFixture);
accountsSuite(startFixture);
socialSuite(startFixture);
