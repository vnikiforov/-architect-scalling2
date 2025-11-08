rs.initiate(
  {
    _id: "configrs",
    configsvr: true,
    members: [
      { _id: 0, host: "config:27017" }
    ]
  }
)