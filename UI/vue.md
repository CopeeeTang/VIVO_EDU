<template>
  <div class="login">
    <div class="div">
      <div class="frame">
        <div class="div-wrapper">
          <div class="text-wrapper">登录</div>
        </div>

        <div class="frame-2">
          <div class="frame-3">
            <div class="input-field">
              <div class="frame-4">
                <div class="text-wrapper-2">账号</div>
                <div class="text-wrapper-3">*</div>
              </div>
              <div class="label-wrapper">
                <div class="label">请输入您的账号</div>
              </div>
            </div>

            <div class="input-field">
              <div class="frame-4">
                <div class="text-wrapper-2">密码</div>
                <div class="text-wrapper-3">*</div>
              </div>
              <div class="input-field-2">
                <div class="label">请输入您的密码</div>
                <img class="img" alt="Frame" src="./frame.svg" />
              </div>
            </div>
          </div>

          <div class="button-wrapper">
            <button class="button">
              <div class="text-wrapper-4">登录</div>
            </button>
          </div>

          <div class="frame-5">
            <img class="line" alt="Line" src="./line-3.svg" />
            <div class="text-wrapper-5">Or</div>
            <img class="line" alt="Line" src="./line-2.svg" />
          </div>

          <div class="frame-6">
            <div class="img-wrapper">
              <img class="img" alt="Devicon google" src="./devicon-google.svg" />
            </div>
            <div class="img-wrapper">
              <img class="img" alt="Ic baseline apple" src="./ic-baseline-apple.svg" />
            </div>
          </div>
        </div>
      </div>

      <p class="p">
        <span class="span">还未拥有账号？</span>
        <span class="text-wrapper-6">立即注册</span>
      </p>

      <div class="status-bar">
        <div class="time">
          <div class="time-wrapper">
            <div class="time-2">9:41</div>
          </div>
        </div>

        <div class="levels">
          <div class="battery">
            <div class="overlap-group">
              <div class="capacity" />
            </div>
            <img class="cap" alt="Cap" src="./cap.svg" />
          </div>
          <img class="wifi" alt="Wifi" src="./wifi.svg" />
          <img class="cellular-connection" alt="Cellular connection" src="./cellular-connection.svg" />
        </div>
      </div>

      <div class="group" />
    </div>
  </div>
</template>

<script>
export default {
  name: "Login",
};
</script>

<style>
.login {
  background-color: #ffffff;
  display: flex;
  flex-direction: row;
  justify-content: center;
  width: 100%;
}

.login .div {
  background-color: #ffffff;
  height: 932px;
  position: relative;
  width: 430px;
}

.login .frame {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 25px;
  left: 25px;
  position: absolute;
  top: 358px;
  width: 380px;
}

.login .div-wrapper {
  align-items: center;
  display: inline-flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 5px;
  position: relative;
}

.login .text-wrapper {
  color: #000000;
  font-family: "YouSheShaYuFeiTeJianKangTi-Regular", Helvetica;
  font-size: 36px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: 48px;
  margin-top: -1.00px;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}

.login .frame-2 {
  align-items: flex-start;
  align-self: stretch;
  border-radius: 15px;
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 25px;
  position: relative;
  width: 100%;
}

.login .frame-3 {
  align-items: flex-start;
  align-self: stretch;
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 25px;
  position: relative;
  width: 100%;
}

.login .input-field {
  align-items: flex-start;
  align-self: stretch;
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 5px;
  position: relative;
  width: 100%;
}

.login .frame-4 {
  align-items: flex-start;
  display: inline-flex;
  flex: 0 0 auto;
  gap: 3px;
  position: relative;
}

.login .text-wrapper-2 {
  color: var(--gray-1);
  font-family: var(--title-h4-font-family);
  font-size: var(--title-h4-font-size);
  font-style: var(--title-h4-font-style);
  font-weight: var(--title-h4-font-weight);
  letter-spacing: var(--title-h4-letter-spacing);
  line-height: var(--title-h4-line-height);
  margin-top: -1.00px;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}

.login .text-wrapper-3 {
  color: var(--red);
  font-family: var(--body-b4-font-family);
  font-size: var(--body-b4-font-size);
  font-style: var(--body-b4-font-style);
  font-weight: var(--body-b4-font-weight);
  letter-spacing: var(--body-b4-letter-spacing);
  line-height: var(--body-b4-line-height);
  margin-top: -1.00px;
  position: relative;
  width: fit-content;
}

.login .label-wrapper {
  align-items: center;
  align-self: stretch;
  border: 1px solid;
  border-color: var(--gray-1);
  border-radius: 25px;
  display: flex;
  flex: 0 0 auto;
  gap: 10px;
  justify-content: space-around;
  padding: 15px;
  position: relative;
  width: 100%;
}

.login .label {
  color: #ababca;
  flex: 1;
  font-family: "PingFang SC-Regular", Helvetica;
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: 26px;
  margin-top: -1.00px;
  position: relative;
}

.login .input-field-2 {
  align-items: center;
  align-self: stretch;
  border: 1px solid;
  border-color: var(--gray-1);
  border-radius: 25px;
  display: flex;
  flex: 0 0 auto;
  justify-content: space-between;
  padding: 15px;
  position: relative;
  width: 100%;
}

.login .img {
  height: 18px;
  position: relative;
  width: 18px;
}

.login .button-wrapper {
  align-items: flex-start;
  align-self: stretch;
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 10px;
  position: relative;
  width: 100%;
}

.login .button {
  all: unset;
  align-items: center;
  align-self: stretch;
  background-color: var(--black);
  border-radius: 35px;
  box-sizing: border-box;
  display: flex;
  flex: 0 0 auto;
  gap: 10px;
  justify-content: center;
  padding: 15px;
  position: relative;
  width: 100%;
}

.login .text-wrapper-4 {
  color: #ffffff;
  font-family: var(--title-h4-font-family);
  font-size: var(--title-h4-font-size);
  font-style: var(--title-h4-font-style);
  font-weight: var(--title-h4-font-weight);
  letter-spacing: var(--title-h4-letter-spacing);
  line-height: var(--title-h4-line-height);
  margin-top: -1.00px;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}

.login .frame-5 {
  align-items: center;
  align-self: stretch;
  display: flex;
  flex: 0 0 auto;
  gap: 15px;
  justify-content: center;
  position: relative;
  width: 100%;
}

.login .line {
  flex: 1;
  flex-grow: 1;
  height: 1px;
  object-fit: cover;
  position: relative;
}

.login .text-wrapper-5 {
  color: var(--gray-1);
  font-family: var(--label-h4-font-family);
  font-size: var(--label-h4-font-size);
  font-style: var(--label-h4-font-style);
  font-weight: var(--label-h4-font-weight);
  letter-spacing: var(--label-h4-letter-spacing);
  line-height: var(--label-h4-line-height);
  margin-top: -1.00px;
  position: relative;
  width: fit-content;
}

.login .frame-6 {
  align-items: flex-start;
  align-self: stretch;
  display: flex;
  flex: 0 0 auto;
  gap: 15px;
  position: relative;
  width: 100%;
}

.login .img-wrapper {
  align-items: center;
  border: 2px solid;
  border-color: var(--black);
  border-radius: 55px;
  display: flex;
  flex: 1;
  flex-grow: 1;
  gap: 10px;
  justify-content: center;
  padding: 15px 25px;
  position: relative;
}

.login .p {
  color: transparent;
  font-family: "YouSheShaYuFeiTeJianKangTi-Regular", Helvetica;
  font-size: 14px;
  font-weight: 400;
  left: 138px;
  letter-spacing: 0;
  line-height: 26px;
  position: absolute;
  top: 893px;
  white-space: nowrap;
}

.login .span {
  color: #374c3c;
}

.login .text-wrapper-6 {
  color: #4793af;
}

.login .status-bar {
  align-items: center;
  display: flex;
  justify-content: space-between;
  left: 0;
  position: absolute;
  top: 0;
  width: 430px;
}

.login .time {
  height: 54px;
  position: relative;
  width: 138px;
}

.login .time-wrapper {
  height: 932px;
  position: relative;
  width: 430px;
}

.login .time-2 {
  color: var(--black);
  font-family: "SF Pro-Semibold", Helvetica;
  font-size: 17px;
  font-weight: 400;
  left: 51px;
  letter-spacing: 0;
  line-height: 22px;
  position: absolute;
  text-align: center;
  top: 17px;
  white-space: nowrap;
}

.login .levels {
  height: 54px;
  position: relative;
  width: 143px;
}

.login .battery {
  height: 13px;
  left: 83px;
  position: absolute;
  top: 23px;
  width: 27px;
}

.login .overlap-group {
  border: 1px solid;
  border-color: var(--black);
  border-radius: 4.3px;
  height: 13px;
  left: 0;
  position: absolute;
  top: 0;
  width: 25px;
}

.login .capacity {
  background-color: var(--black);
  border-radius: 2.5px;
  height: 9px;
  left: 1px;
  position: relative;
  top: 1px;
  width: 21px;
}

.login .cap {
  height: 4px;
  left: 26px;
  position: absolute;
  top: 5px;
  width: 1px;
}

.login .wifi {
  height: 12px;
  left: 59px;
  position: absolute;
  top: 24px;
  width: 17px;
}

.login .cellular-connection {
  height: 12px;
  left: 32px;
  position: absolute;
  top: 24px;
  width: 19px;
}

.login .group {
  background-color: var(--green);
  border-radius: 89px;
  height: 178px;
  left: 126px;
  position: absolute;
  top: 96px;
  width: 178px;
}
</style>