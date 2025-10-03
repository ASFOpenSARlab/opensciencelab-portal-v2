class Common {
  constructor(id, getApiUri, postApiUri) {
    this.id = id;
    this.getApiUri = getApiUri;
    this.postApiUri = postApiUri;
    this.store = $state({});
  }

  pull = async () => {
    const response = await fetch(this.getApiUri, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(response);
    }

    const data = await response.json();
    this.data = data;

    return data;
  };

  push = async () => {
    const response = await fetch(this.postApiUri, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(this.data),
    });

    if (!response.ok) {
      throw new Error(response);
    }

    const result = await response.json();
    return result;
  };

  get data() {
    return this.store[this.id];
  }

  set data(newData) {
    this.store[this.id] = newData;
  }
}

export class UserClass extends Common {
  constructor() {
    super(
      Symbol("UserClass"),
      "/portal/users/example",
      "/portal/users/example"
    );
  }
}
