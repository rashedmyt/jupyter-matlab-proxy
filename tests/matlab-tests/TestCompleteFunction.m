% Copyright 2024-2026 The MathWorks, Inc.

classdef TestCompleteFunction < matlab.unittest.TestCase
% TestCompleteFunction contains unit tests for the complete function

    properties
        TestPaths
    end

    methods (TestClassSetup)
        function addFunctionPath(testCase)
            testCase.TestPaths = cellfun(@(relative_path)(fullfile(pwd, relative_path)), {"../../src/jupyter_matlab_kernel/matlab", "../../tests/matlab-tests/"}, 'UniformOutput', false);
            cellfun(@addpath, testCase.TestPaths)
        end
    end

    methods (TestClassTeardown)
        function removeFunctionPath(testCase)
            cellfun(@rmpath, testCase.TestPaths)
        end
    end

    methods (Test)
        function testBasicCompletion(testCase)
        % Test basic completion functionality
            code = 'plo';
            cursorPosition = 3;
            result = jupyter.complete(code, cursorPosition);
            expectedMatches = 'plot';
            testCase.verifyTrue(ismember(expectedMatches, result.matches), "Completion 'plot' was not found in the result");
            % Verify start and end positions - uses 0-based indexing for Jupyter compatibility
            % getStartPosition walks back to find word start; for 'plo' at cursor 3, start=0, end=3
            testCase.verifyEqual(result.start, 0, "Start position should be 0 for completing 'plo'");
            testCase.verifyEqual(result.end, 3, "End position should equal cursor position");
        end

        function testEmptyCode(testCase)
        % Test behavior with empty code string
            code = '';
            cursorPosition = 0;
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
            % When no completions, start and end should equal cursor position
            testCase.verifyEqual(result.start, cursorPosition, "Start should equal cursor when no matches");
            testCase.verifyEqual(result.end, cursorPosition, "End should equal cursor when no matches");
        end

        function testInvalidCursorPosition(testCase)
        % Test behavior with an invalid cursor position
            code = 'plot';
            cursorPosition = -1; % Invalid cursor position
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
            % When no completions, start and end should equal cursor position
            testCase.verifyEqual(result.start, cursorPosition, "Start should equal cursor when no matches");
            testCase.verifyEqual(result.end, cursorPosition, "End should equal cursor when no matches");
        end

        function testCompletionStartEndWithLeadingWhitespace(testCase)
        % Test that start position correctly identifies word start after whitespace
            code = '  plo';
            cursorPosition = 5;
            result = jupyter.complete(code, cursorPosition);
            expectedMatches = 'plot';
            testCase.verifyTrue(ismember(expectedMatches, result.matches), ...
                "Completion 'plot' was not found in the result");
            % getStartPosition breaks on whitespace - start should be 2 (position of the first letter)
            % The range "  plo" (positions 2-5) gets replaced with "plot"
            testCase.verifyEqual(result.start, 2, ...
                "Start should be 2 (not walking back the whitespace) for '  plo'");
            testCase.verifyEqual(result.end, 5, ...
                "End should equal cursor position");
        end

        function testCompletionStartEndPartialWord(testCase)
        % Test start/end for partial word completion (cursor in middle of word)
            code = 'plot';
            cursorPosition = 2;
            result = jupyter.complete(code, cursorPosition);
            % Completing 'pl' - start should be 0, end should be 2
            testCase.verifyEqual(result.start, 0, ...
                "Start position should be equal to 0");
            testCase.verifyEqual(result.end, cursorPosition, ...
                "End position should equal cursor position");
            testCase.verifyTrue(ismember('plot', result.matches), ...
                "Completion 'plot' should be in matches for 'pl'");
        end

        function testCompletionAfterAssignmentOperator(testCase)
        % Test that start position stops at '=' so only the RHS token is replaced.
        % For 'a=pea' completed to 'peaks', Jupyter should produce 'a=peaks',
        % not replace the entire string.
            code = 'a=pea';
            cursorPosition = 5;
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(ismember('peaks', result.matches), ...
                "Completion 'peaks' was not found in the result");
            % 'pea' starts at position 3 (1-indexed) = position 2 (0-indexed).
            % getStartPosition must stop at '=' and return 2, not walk back to 0.
            testCase.verifyEqual(result.start, 2, ...
                "Start should be 2 (stopping at '=') so only 'pea' is replaced");
            testCase.verifyEqual(result.end, 5, ...
                "End should equal cursor position");
        end
    end
end
