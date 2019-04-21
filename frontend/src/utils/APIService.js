import axios from 'axios';

import AuthService from './AuthService';

class APIService {
  constructor(apiURL) {
    this.authService = new AuthService(apiURL);
  }

  getAbout() {
    this.cancelAbout();
    this.aboutCall = axios.CancelToken.source();
    const axiosConfig = { cancelToken: this.aboutCall.token };

    return this.authService.apiCall('/about', axiosConfig);
  }

  cancelAbout() {
    if (this.aboutCall) {
      this.aboutCall.cancel();
    }
  }

  getSecretQuestions(page = 1, perPage = 10, enabled = null, cancel = true) {
    let axiosConfig = {};
    if (cancel) {
      this.cancelGetSecretQuestions();
      this.getSecretQuestionsCall = axios.CancelToken.source();
      axiosConfig = { cancelToken: this.getSecretQuestionsCall.token };
    }

    let url = `/questions?page=${page}&per_page=${perPage}`;
    if (enabled != null) {
      url = `${url}&enabled=${enabled}`;
    }
    return this.authService.apiCall(url, axiosConfig);
  }

  cancelGetSecretQuestions() {
    if (this.getSecretQuestionsCall) {
      this.getSecretQuestionsCall.cancel();
    }
  }

  getAllEnabledSecretQuestions() {
    return new Promise((resolve, reject) => {
      let items = [];
      this.getSecretQuestions(1, 0, true)
        .then((data) => {
          const count = data.meta.total;
          // Calculate how many pages there are when 50 are fetched at a time
          const pages = Math.ceil(count / 50);
          let page = 1;
          const promises = [];
          while (page <= pages) {
            promises.push(this.getSecretQuestions(page, 50, true, false));
            page += 1;
          }
          Promise.all(promises)
            .then((apiPages) => {
              apiPages.forEach((apiPage) => {
                items = items.concat(apiPage.items);
              });
              resolve(items);
            })
            .catch((error) => {
              reject(error);
            });
        })
        .catch((error) => {
          reject(error);
        });
    });
  }

  addSecretQuestion(question) {
    const axiosConfig = {
      method: 'post',
      data: { question },
    };
    return this.authService.authenticatedAPICall('/questions', axiosConfig, 'admin');
  }

  patchSecretQuestion(questionID, data) {
    const axiosConfig = {
      method: 'patch',
      data,
    };
    return this.authService.authenticatedAPICall(`/questions/${questionID}`, axiosConfig, 'admin');
  }

  getAnswers() {
    // Assumes there's no way the user is required to answer more than 100 questions
    return this.authService.authenticatedAPICall('/answers?per_page=100', null, 'user');
  }

  setAnswers(answers) {
    const axiosConfig = {
      method: 'post',
      data: answers,
    };
    return this.authService.authenticatedAPICall('/answers', axiosConfig, 'user');
  }

  deleteAnswers() {
    const axiosConfig = { method: 'delete' };
    return this.authService.authenticatedAPICall('/answers', axiosConfig, 'user');
  }
}

export default APIService;
