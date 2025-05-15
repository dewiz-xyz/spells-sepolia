// SPDX-FileCopyrightText: © 2020 Dai Foundation <www.daifoundation.org>
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

pragma solidity 0.8.16;

import "./DssExec.sol";
import "dss-exec-lib/DssAction.sol";

import { GemAbstract } from "dss-interfaces/ERC/GemAbstract.sol";

import { LibInit } from "./dependencies/LibInit.sol";

interface DaiUsdsLike {
    function daiToUsds(address usr, uint256 wad) external;
}

interface MkrSkyLike {
    function mkrToSky(address usr, uint256 wad) external;
    function rate() external view returns (uint256);
}

interface PauseLike {
    function setDelay(uint256) external;
}

interface LitePsmLike {
    function kiss(address) external;
}

interface ProxyLike {
    function exec(address target, bytes calldata args) external payable returns (bytes memory out);
}

contract DssSpellAction is DssAction {
    // Provides a descriptive tag for bot consumption
    // This should be modified weekly to provide a summary of the actions
    // Hash: cast keccak -- "$(wget 'https://raw.githubusercontent.com/makerdao/community/4ee57431afa70c85f5c643922a7cd066619f1927/governance/votes/Executive%20Vote%20-%20April%2030%2C%202025.md' -q -O - 2>/dev/null)"
    string public constant override description = "2025-05-13 MakerDAO Executive Spell | Hash: TODO";

    // Set office hours according to the summary
    function officeHours() public pure override returns (bool) {
        return true;
    }

    // ---------- Rates ----------
    // Many of the settings that change weekly rely on the rate accumulator
    // described at https://docs.makerdao.com/smart-contract-modules/rates-module
    // To check this yourself, use the following rate calculation (example 8%):
    //
    // $ bc -l <<< 'scale=27; e( l(1.08)/(60 * 60 * 24 * 365) )'
    //
    // A table of rates can be found at
    //    https://ipfs.io/ipfs/QmVp4mhhbwWGTfbh2BzwQB9eiBrQBKiqcPRZCaAxNUaar6
    //
    // uint256 internal constant X_PCT_RATE = ;

    // ---------- Math ----------

    // ---------- Contracts ----------

    // ---------- Wallets ----------

    // ---------- Constant Values ----------

    // ---------- Spark Proxy Spell ----------
    // Spark Proxy: https://github.com/marsfoundation/sparklend-deployments/blob/bba4c57d54deb6a14490b897c12a949aa035a99b/script/output/1/primary-sce-latest.json#L2

    // ---------- STAR2 Proxy Spell ----------
    // Note: The deployment address for the Bloom Proxy can be found at https://forum.sky.money/t/technical-scope-of-the-star-2-allocator-launch/26190

    uint256 internal constant NONCE = 21;

    function actions() public override {
        LibInit.init();
    }
}

contract DssSpell is DssExec {
    constructor() DssExec(block.timestamp + 30 days, address(new DssSpellAction())) {}
}
