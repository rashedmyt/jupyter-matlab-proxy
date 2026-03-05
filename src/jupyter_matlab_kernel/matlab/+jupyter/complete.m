% IMPORTANT NOTICE:
% This file may contain calls to MathWorks internal APIs which are subject to
% change without any prior notice. Usage of these undocumented APIs outside of
% these files is not supported.

function result = complete(code, cursorPosition)
% COMPLETE A helper function to provide tab completion results

% Copyright 2023-2026 The MathWorks, Inc.

% Get tab completion data for matlab code. Using evalin('base',..) so that the
% function workspace does not affect the results.
completionCmd = ['builtin(''_programmingAidsTest'','''',' mat2str(code) ',' mat2str(cursorPosition) ', [])'];
completionData = jsondecode(evalin('base', completionCmd));

startPosition = getStartPosition(code, cursorPosition);

[result.matches, result.completions] = getCompletions(completionData, cursorPosition, startPosition);

if isfield(completionData, "signatures")
    signatures = completionData.signatures;

    if ~iscell(signatures)
        signatures = {signatures};
    end

    for idx1 = 1:length(signatures)
        inputArguments = signatures{idx1}.inputArguments;

        if ~iscell(inputArguments)
            inputArguments = {inputArguments};
        end

        for idx2 = 1:length(inputArguments)
            [matches, completions] = getCompletions(inputArguments{idx2}, cursorPosition, startPosition);

            % Append matches and completions to the original output.
            result.matches = [result.matches matches];
            result.completions = [result.completions completions];
        end
    end
end

if ~isempty(result.completions)
    result.start = result.completions{1}.start;
    result.end = result.completions{1}.end;
else
    result.start = cursorPosition;
    result.end = cursorPosition;
end

% Helper function to extract the necessary completion information from the
% provided completion data.
function [matches, completions] = getCompletions(completionData, cursorPosition, startPosition)
matches = cell(0);
completions = cell(0);

if isfield(completionData, "widgetData")
    if isfield(completionData.widgetData, "choices")
        choices = completionData.widgetData.choices;

        is_choices_struct = isstruct(choices);

        for idx = 1:length(choices)
            if is_choices_struct
                choice = choices(idx);
            else
                choice = choices{idx};
            end

            % Live Editor tasks are not available in Jupyter. Ignore these
            % suggestions
            if isfield(choice, "completion") && ~strcmp(choice.matchType, 'mlappFile')
                matches{end+1} = choice.completion;
                completion.text = choice.completion;
                completion.type = getCompletionType(choice.matchType);
                completion.start = startPosition;
                completion.end = cursorPosition;
                completions{end+1} = completion;
            end
        end
    end
end

% Helper function to consolidate different types of suggestions to a minimal
% set. This data is extracted from LSP.
function type = getCompletionType(inputType)
if any(strcmp(inputType, ["unknown","mFile","pFile","mlxFile","mlappFile",...
                        "mex","mdlFile","slxFile","slxpFile","sscFile",...
                        "sscpFile","function","localFunction"]))
    type = "function";
elseif any(strcmp(inputType, ["literal","username","feature","messageId"]))
    type = "text";
elseif any(strcmp(inputType, ["pathItem","filename"]))
    type = "file";
elseif any(strcmp(inputType, ["keyword", "attribute"]))
    type = "keyword";
elseif any(strcmp(inputType, ["class", "sfxFile"]))
    type = "class";
elseif any(strcmp(inputType, ["logical","cellString"]))
    type = "value";
elseif strcmp(inputType, "folder")
    type = "folder";
elseif strcmp(inputType, "fieldname")
    type = "field";
elseif strcmp(inputType, "package")
    type = "package";
elseif strcmp(inputType, "method")
    type = "method";
elseif strcmp(inputType, "enumeration")
    type = "enum";
elseif strcmp(inputType, "property")
    type = "property";
elseif strcmp(inputType, "variable")
    type = "variable";
else
    type = "function";
end

% Helper function to get the start position of the cursor in the code from which to start the completion
function startPosition = getStartPosition(code, cursorPosition)
currentPosition = cursorPosition;
while currentPosition > 0
    % Stop on any character that is not a word character (letter, digit, or underscore).
    % This ensures operators like '=' do not get included in the replaced range.
    if isempty(regexp(code(currentPosition), '^\w$', 'once'))
        break;
    end
    currentPosition = currentPosition - 1;
end
startPosition = currentPosition;
