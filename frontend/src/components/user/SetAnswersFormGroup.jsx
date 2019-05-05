import React, { Component } from 'react';
import { PropTypes } from 'prop-types';
import { FormGroup, Input, Label } from 'reactstrap';

import PasswordInput from '../common/PasswordInput';
import './SetAnswersFormGroup.css';

/**
 * Creates a form group consisting of a questions select input and answer text input.
 *
 * @class SetAnswersFormGroup
 * @extends {Component}
 */
class SetAnswersFormGroup extends Component {
  static propTypes = {
    configured: PropTypes.bool.isRequired,
    handleInput: PropTypes.func.isRequired,
    handleSelect: PropTypes.func.isRequired,
    loading: PropTypes.bool,
    questions: PropTypes.array.isRequired,
    questionNumber: PropTypes.number.isRequired,
  };

  static defaultProps = {
    loading: false,
  };

  /**
   * Toggles the visibility of the answer input field.
   */
  toggleVisibility = () => {
    this.setState(oldState => ({ visible: !oldState.visible }));
  };

  /**
   * Return the JSX of the component to render.
   */
  render() {
    const {
      configured,
      handleInput,
      handleSelect,
      loading,
      questions,
      questionNumber,
    } = this.props;

    // Create an option for each possible question
    const questionOptions = questions.map(question => (
      <option key={question.id} data-id={question.id}>
        {question.question}
      </option>
    ));

    // The question indexes start at 0, but the user should see 1 instead
    const displayQuestionNumber = questionNumber + 1;
    return (
      <FormGroup key={displayQuestionNumber} className="mb-4">
        <Label for={`question${displayQuestionNumber}`} className="question-label">
          {`Question ${displayQuestionNumber}:`}
        </Label>
        <Input
          className="question-input"
          disabled={configured || loading}
          data-id={questionNumber}
          id={`question${displayQuestionNumber}`}
          name={`select${displayQuestionNumber}`}
          onChange={handleSelect}
          required={!configured}
          type="select"
        >
          {questionOptions}
        </Input>
        <PasswordInput
          className="mt-2 question-input"
          data-id={questionNumber}
          disabled={configured || loading}
          name={`answer${displayQuestionNumber}`}
          onChange={handleInput}
          placeholder={configured ? 'Your answer is set' : 'Please enter an answer'}
          required={!configured}
        />
      </FormGroup>
    );
  }
}

export default SetAnswersFormGroup;
