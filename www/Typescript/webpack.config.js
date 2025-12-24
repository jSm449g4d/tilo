const path = require("path");
const entry = require("webpack-glob-entry");

module.exports = {
  entry: entry("./tsx/index.tsx"),
  output: {
    path: path.resolve(__dirname, "../"),
    filename: "./html/static/src/main.js",
  },

  mode: "production",
  devtool: "source-map",

  resolve: {
    extensions: [".js", ".ts", ".tsx"],
  },

  module: {
    rules: [
      { exclude: /node_modules/, test: /\.ts(x?)$/, use: ["ts-loader"] },
      { enforce: "pre", test: /\.js$/, use: "source-map-loader" },
      { test: /\.css$/, use: ["style-loader", "css-loader"] },
      {
        test: /\.s[ac]ss$/,
        use: ["style-loader", "css-loader", "sass-loader"],
      },
    ],
  },
/*
  externals: {
    react: "React",
    "react-dom": "ReactDOM",
    recharts: "Recharts",
  },
*/ 
};