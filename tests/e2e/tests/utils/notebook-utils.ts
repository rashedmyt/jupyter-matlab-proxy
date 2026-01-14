// Copyright 2026 The MathWorks, Inc.

import { expect, IJupyterLabPageFixture } from '@jupyterlab/galata';

const NEW_SESSION_COMMAND = '%%matlab new_session';
const NEW_SESSION_OUTPUT =
    'A dedicated MATLAB session has been started for this kernel';

/**
 * Creates a new Jupyter notebook with the MATLAB kernel.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name for the new notebook
 */
export async function createNotebook (
    page: IJupyterLabPageFixture,
    notebookName: string
) {
    await page.notebook.createNew(notebookName, {
        kernel: 'jupyter_matlab_kernel'
    });
    await page.notebook.isOpen(notebookName);
    await page.notebook.isActive(notebookName);
}

/**
 * Creates an isolated MATLAB session using the %%matlab new_session command.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook to create the isolated session in
 */
export async function createIsolatedMATLABSession (
    page: IJupyterLabPageFixture,
    notebookName: string
) {
    await runCommand(page, notebookName, NEW_SESSION_COMMAND);
    await verifyOutputContains(page, notebookName, NEW_SESSION_OUTPUT);
}

/**
 * Clicks the "Open MATLAB" toolbar button.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook containing the button
 */
export async function clickOpenMATLABButton (
    page: IJupyterLabPageFixture,
    notebookName: string
) {
    await page.notebook.activate(notebookName);
    await page.notebook
        .getToolbarItemLocator('matlabToolbarButton')
        .then((item) => item?.click());
}

/**
 * Executes a command in the first cell of the specified notebook.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook to run the command in
 * @param command - MATLAB command or magic command to execute
 */
export async function runCommand (
    page: IJupyterLabPageFixture,
    notebookName: string,
    command: string
) {
    await page.notebook.activate(notebookName);
    await page.notebook.setCell(0, 'code', command);
    await page.notebook.runCell(0);
}

/**
 * Verifies that the output of the first cell contains the expected text.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook to check
 * @param expectedOutput - Expected text in the cell output
 */
export async function verifyOutputContains (
    page: IJupyterLabPageFixture,
    notebookName: string,
    expectedOutput: string
) {
    await page.notebook.activate(notebookName);
    const cellOutput = (await page.notebook.getCellTextOutput(0)) ?? [''];
    expect(cellOutput.length).toBeGreaterThan(0);
    expect(cellOutput[0]).toContain(expectedOutput);
}
