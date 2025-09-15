import json
import config
import requests


class NGAClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.UA,
                "Cookie": f"ngaPassportUid={config.NGAPASSPORTUID}; ngaPassportCid={config.NGAPASSPORTCID};",
            }
        )
        self.base_url = config.BASE_URL

    def get_page(self, tid, aid, page):
        if not tid and not page:
            raise ValueError("Either tid or page must be provided.")
        if page < 1:
            raise ValueError("Page number must be greater than 0.")
        """
        go代码：
        {
                resp, err = Client.R().SetFormData(map[string]string{
                        "page":     cast.ToString(page),
                        "tid":      cast.ToString(tiezi.Tid),
                        "authorid": cast.ToString(tiezi.AuthorId),
                }).Post("app_api.php?__lib=post&__act=list")
        }
        """
        url = f"{self.base_url}/app_api.php?__lib=post&__act=list"
        data = {
            "page": str(page),
            "tid": str(tid),
        }
        if aid:
            data["authorid"] = str(aid)
        response = self.session.post(url, data=data)
        response.raise_for_status()

        json_data = response.json()

        if json_data.get("code")!=0:
            raise Exception(f"Error fetching page: {json_data.get('msg', 'Unknown error')}")

        #保存到tmp.json
        #with open("tmp.json", "w", encoding="utf-8") as f:
        #    json.dump(json_data, f, ensure_ascii=False, indent=4)

        return json_data

    def get_ngahtml(self,tid,aid,page):
        if not tid and not page:
            raise ValueError("Either pid or page must be provided.")
        if page < 1:
            raise ValueError("Page number must be greater than 0.")
        url = f"{self.base_url}/read.php?tid={tid}&authorid={aid}&page={page}&rand=556"
        response = self.session.get(url)
        response.raise_for_status()