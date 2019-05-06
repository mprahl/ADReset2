import React, { Component } from 'react';
import { PropTypes } from 'prop-types';
import { Card, CardBody, CardHeader, Container, Form, FormGroup } from 'reactstrap';
import ExitToApp from '@material-ui/icons/ExitToApp';
import Undo from '@material-ui/icons/Undo';

import APIService from '../../utils/APIService';
import IconButton from '../common/IconButton';
import SetAnswersFormGroup from './SetAnswersFormGroup';
import Spinner from '../common/Spinner';

class SetAnswers extends Component {
  static propTypes = {
    about: PropTypes.object.isRequired,
    displayToast: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      configured: false,
      initialLoading: true,
      setLoading: false,
      resetLoading: false,
      fatalError: false,
      selectedQuestions: [],
      selectedAnswers: [],
      questions: [],
    };
    // TODO: Pass in a configurable API URL
    this.apiService = new APIService();
  }

  componentDidMount() {
    // Once the component mounts, query the API
    this.initialize();
  }

  /**
   * Stores the selected question in the state.
   *
   * @param {*} event The event that triggered this handler.
   */
  handleSelect = event => {
    const select = event.target;
    const inputID = parseInt(select.attributes['data-id'].value, 10);
    const selectedQuestionID = parseInt(
      select.options[select.selectedIndex].attributes['data-id'].value,
      10,
    );
    this.setState(oldState => {
      const selectedQuestions = oldState.selectedQuestions.slice();
      selectedQuestions[inputID] = selectedQuestionID;
      return { selectedQuestions };
    });
  };

  /**
   * Stores the user's answers in the state.
   *
   * @param {*} event The event that triggered this handler.
   */
  handleInput = event => {
    const input = event.target;
    const inputID = parseInt(input.attributes['data-id'].value, 10);
    this.setState(oldState => {
      const selectedAnswers = oldState.selectedAnswers.slice();
      selectedAnswers[inputID] = input.value.trim();
      return { selectedAnswers };
    });
  };

  /**
   * Submits the selected questions and answers to the API.
   *
   * @param {*} event The event that triggered this handler.
   */
  handleSubmit = event => {
    event.preventDefault();
    const { selectedQuestions, selectedAnswers } = this.state;
    const answers = selectedAnswers.map((answer, inputID) => ({
      question_id: selectedQuestions[inputID],
      answer,
    }));
    this.setState({ setLoading: true });
    this.apiService
      .setAnswers(answers)
      .then(() => {
        const form = document.getElementById('js-answer-form');
        form.reset();
        this.initialize();
      })
      .catch(error => {
        this.props.displayToast('error', error.message);
        this.setState({ setLoading: false });
      });
  };

  /**
   * Deletes the user's configured answers using the API.
   *
   * @param {*} event The event that triggered this handler.
   */
  handleReset = event => {
    event.preventDefault();
    this.setState({ resetLoading: true });
    this.apiService
      .deleteAnswers()
      .then(() => {
        this.props.displayToast('info', 'Your answers were reset successfully');
        this.initialize();
      })
      .catch(error => {
        this.props.displayToast('error', error.message);
        this.setState({ resetLoading: false });
      });
  };

  /**
   * Initialize the React state with the user's state in the API.
   */
  initialize() {
    const { about } = this.props;
    // Get the user's answers to know if they are configured or not
    this.apiService
      .getAnswers()
      .then(answersRv => {
        const answers = answersRv.items;
        // If the user has configured their answers in the past, then show them which questions they
        // chose
        if (answers.length > 0) {
          // If the user previously set their answers, and the administrator raised the required
          // amount of questions, then notify the user
          if (answers.length < about.required_answers) {
            this.props.displayToast(
              'error',
              'The administrator raised the number of required answers. Please reset your answers '
                + 'and set them again.',
            );
          }

          // The selected questions will just be the ones the user configured in the past.
          const selectedQuestions = [];
          // Since the user is already configured, it's not necessary to get all the available
          // questions from the API. Instead, just collect the ones that were previously answered.
          const questions = answers.map((answer, inputID) => {
            selectedQuestions[inputID] = answer.question.id;
            return answer.question;
          });
          this.setState({
            configured: true,
            initialLoading: false,
            questions,
            resetLoading: false,
            selectedQuestions,
            setLoading: false,
          });
          this.props.displayToast('info', 'Your answers are set. Click on "Reset" to change them.');
          return;
        }

        // If the code reaches here, that means the user has not previously configured their
        // questions. Because of that, it's necessary to get all the available questions they can
        // choose to answer.
        this.apiService
          .getAllEnabledSecretQuestions()
          .then(questions => {
            const { selectedQuestions } = this.state;
            // Only set the defaults if it hasn't been previously set before. For instance,
            // if the user resets their answers, the selected questions in the UI remain the same,
            // and that needs to still be reflected in the component state.
            if (!selectedQuestions.length) {
              // By default, just select the first `about.required_answers` questions as the select
              // options in the UI
              for (let i = 0; i < about.required_answers; i += 1) {
                selectedQuestions[i] = questions[i].id;
              }
            }
            this.setState({
              questions,
              selectedQuestions,
              configured: false,
            });
          })
          .catch(error => {
            this.props.displayToast('error', error.message);
            // If the query to get all the questions fails, then there's nothing the UI can do
            this.setState({ fatalError: true });
          })
          .finally(() => {
            this.setState({ initialLoading: false, setLoading: false, resetLoading: false });
          });
      })
      .catch(error => {
        this.props.displayToast('error', error.message);
        // If the query to get the user's configured answers fails, then there's nothing the UI
        // can do
        this.setState({
          fatalError: true,
          initialLoading: false,
          setLoading: false,
          resetLoading: false,
        });
      });
  }

  /**
   * Return the JSX of the component to render.
   */
  render() {
    // When the component is first loaded, just load the spinner while the API is queried
    if (this.state.initialLoading === true) {
      return <Spinner />;
    }

    const header = <h2 className="text-center mb-5">Secret Questions and Answers</h2>;
    // If a fatal error is encountered, just return the page header
    if (this.state.fatalError) {
      return <Container>{header}</Container>;
    }

    const { about } = this.props;
    const { configured, questions, selectedQuestions, setLoading, resetLoading } = this.state;

    const questionFormGroups = [];
    // If the user already configured their answers, then only display the number of questions
    // that were previously configured. If the user has not set their answers, then display
    // `about.required_answers` questions.
    const numQuestionsToDisplay = configured ? questions.length : about.required_answers;
    for (let i = 0; i < numQuestionsToDisplay; i += 1) {
      // Filter the question options so that there is no questions overlapping between selects.
      // This will run every time the user selects a different question.
      const questionOptions = questions.filter(
        q => selectedQuestions[i] === q.id || !selectedQuestions.includes(q.id),
      );
      // Generate a select and input for each configured or required question
      questionFormGroups.push(
        <SetAnswersFormGroup
          configured={configured}
          handleInput={this.handleInput}
          handleSelect={this.handleSelect}
          key={i}
          loading={setLoading}
          minLength={about.answers_minimum_length}
          questions={questionOptions}
          questionNumber={i}
        />,
      );
    }

    return (
      <Container>
        {header}
        <Card className="custom-card">
          <CardHeader>Set Your Secret Questions</CardHeader>
          <CardBody>
            <Form id="js-answer-form" onSubmit={this.handleSubmit}>
              {questionFormGroups}
              <FormGroup className="mt-5">
                <IconButton
                  disabled={setLoading || resetLoading || configured === true}
                  loading={setLoading}
                  Icon={ExitToApp}
                  primary={configured === false}
                >
                  Submit
                </IconButton>
                <IconButton
                  clickHandler={this.handleReset}
                  disabled={setLoading || resetLoading || configured === false}
                  loading={resetLoading}
                  Icon={Undo}
                  primary={configured === true}
                >
                  Reset
                </IconButton>
              </FormGroup>
            </Form>
          </CardBody>
        </Card>
      </Container>
    );
  }
}

export default SetAnswers;
