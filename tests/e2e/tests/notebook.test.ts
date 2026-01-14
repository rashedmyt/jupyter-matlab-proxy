// Copyright 2026 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';
import * as Utils from './utils/notebook-utils';

// Test timeout set to 2 minutes to accommodate MATLAB startup time
const TEST_TIMEOUT = 2 * 60 * 1000;

// Test notebook names used throughout the test suite
const NOTEBOOK = {
    DEFAULT: 'default-matlab.ipynb', // Notebook using default shared MATLAB session
    ISOLATED: 'isolated-matlab.ipynb', // Notebook using isolated MATLAB session
    NEW: 'new-notebook.ipynb' // New notebook for testing variable sharing
};

interface TestCase {
    name: string;
    command: string;
    output: string;
}

test.describe('Default MATLAB mode', () => {
    test.beforeEach(async ({ page }) => {
        test.setTimeout(TEST_TIMEOUT);
        await Utils.createNotebook(page, NOTEBOOK.DEFAULT);
    });

    const TEST_CASES: TestCase[] = [
        {
            name: 'Ver command produces correct output',
            command: 'ver',
            output: 'MATLAB License Number'
        },
        {
            name: 'Info command produces correct output',
            command: '%%matlab info',
            output: 'MATLAB Shared With Other Notebooks: True'
        }
    ];

    for (const testCase of TEST_CASES) {
        test(testCase.name, async ({ page }) => {
            await Utils.runCommand(page, NOTEBOOK.DEFAULT, testCase.command);
            await Utils.verifyOutputContains(
                page,
                NOTEBOOK.DEFAULT,
                testCase.output
            );
        });
    }

    test('Open MATLAB button points to default MATLAB', async ({
        page,
        context
    }) => {
        const pagePromise = context.waitForEvent('page');
        await Utils.clickOpenMATLABButton(page, NOTEBOOK.DEFAULT);
        const newPage = await pagePromise;
        // Verify the URL points to default MATLAB
        await expect(newPage).toHaveURL(/\/matlab\/default\/index\.html$/);
    });

    test('Calling new_session command after running MATLAB commands raise error', async ({
        page
    }) => {
        // Run a MATLAB command first
        await Utils.runCommand(page, NOTEBOOK.DEFAULT, 'sharedVar = 40 + 2');
        await Utils.verifyOutputContains(
            page,
            NOTEBOOK.DEFAULT,
            'sharedVar = 42'
        );
        // Ensure that new_session command raises error
        await Utils.runCommand(page, NOTEBOOK.DEFAULT, '%%matlab new_session');
        await Utils.verifyOutputContains(
            page,
            NOTEBOOK.DEFAULT,
            'This notebook is currently linked to Default MATLAB session'
        );
    });

    test('Variables are shared across notebooks', async ({ page }) => {
        // Create new variable in one notebook
        await Utils.runCommand(page, NOTEBOOK.DEFAULT, 'sharedVar = 40 + 3');
        await Utils.verifyOutputContains(
            page,
            NOTEBOOK.DEFAULT,
            'sharedVar = 43'
        );
        // Ensure that variable is shared across notebooks
        await Utils.createNotebook(page, NOTEBOOK.NEW);
        await Utils.runCommand(page, NOTEBOOK.NEW, 'sharedVar');
        await Utils.verifyOutputContains(page, NOTEBOOK.NEW, 'sharedVar = 43');
    });
});

test.describe('Isolated MATLAB mode', () => {
    test.beforeEach(async ({ page }) => {
        test.setTimeout(TEST_TIMEOUT);
        await Utils.createNotebook(page, NOTEBOOK.ISOLATED);
        await Utils.createIsolatedMATLABSession(page, NOTEBOOK.ISOLATED);
    });

    const TEST_CASES: TestCase[] = [
        {
            name: 'Info command produces correct output',
            command: '%%matlab info',
            output: 'MATLAB Shared With Other Notebooks: False'
        },
        {
            name: 'New session command again produces correct output',
            command: '%%matlab new_session',
            output: 'This kernel is already using a dedicated MATLAB'
        }
    ];

    for (const testCase of TEST_CASES) {
        test(testCase.name, async ({ page }) => {
            await Utils.runCommand(page, NOTEBOOK.ISOLATED, testCase.command);
            await Utils.verifyOutputContains(
                page,
                NOTEBOOK.ISOLATED,
                testCase.output
            );
        });
    }

    test('Open MATLAB button points to isolated MATLAB', async ({
        page,
        context
    }) => {
        const pagePromise = context.waitForEvent('page');
        await Utils.clickOpenMATLABButton(page, NOTEBOOK.ISOLATED);
        const newPage = await pagePromise;
        // Verify the URL contains a session identifier
        await expect(newPage).toHaveURL(/\/matlab\/[\w-]+\/index\.html$/);
    });

    test('Variables are not shared across notebooks', async ({ page }) => {
        // Create new variable in isolated notebook
        await Utils.runCommand(page, NOTEBOOK.ISOLATED, 'isolatedVar = 40 + 2');
        await Utils.verifyOutputContains(
            page,
            NOTEBOOK.ISOLATED,
            'isolatedVar = 42'
        );
        // Ensure that variable is not shared across notebooks
        await Utils.createNotebook(page, NOTEBOOK.NEW);
        await Utils.runCommand(page, NOTEBOOK.NEW, 'isolatedVar');
        await Utils.verifyOutputContains(
            page,
            NOTEBOOK.NEW,
            "Unrecognized function or variable 'isolatedVar'"
        );
    });
});
