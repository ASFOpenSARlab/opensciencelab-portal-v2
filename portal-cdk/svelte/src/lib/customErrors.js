class PageNotFoundError extends Error {
  constructor(message) {
    super(message);
    this.name = "PageNotFoundError";
    this.status = 404;
  }
}

class ForbiddenError extends Error {
  constructor(message) {
    super(message);
    this.name = "ForbiddenError";
    this.status = 403;
  }
}

class UnauthorizedError extends Error {
  constructor(message) {
    super(message);
    this.name = "UnauthorizedError";
    this.status = 401;
  }
}

export const customErrorTypes = {
  PageNotFoundError: "PageNotFoundError",
  ForbiddenError: "ForbiddenError",
  UnauthorizedError: "UnauthorizedError",
};

export const customError = (response) => {
  if (response.status === 404) {
    throw new PageNotFoundError(response.url);
  }
  if (response.status === 403) {
    throw new ForbiddenError(response.url);
  }
  if (response.status === 401) {
    throw new UnauthorizedError(response.url);
  }
};
