# 概要

分割動画の連結時刻からpart内のローカル時刻を逆引きする処理が、part境界で1秒ずれる。

# 期待動作

work_time_msがpart境界上にある場合、次partのlocal_time_ms=0として解決される。

# 実際の動作

part境界上の時刻が前partの末尾として扱われることがある。

# 再現手順

1. 2part構成のfixtureを使う
2. part1のdurationと同じwork_time_msを指定する
3. work_time_to_video_timeを実行する

# 受け入れ条件

- [ ] 境界時刻が次partのlocal_time_ms=0になる
- [ ] 境界直前は前partの末尾になる
- [ ] unit testが追加される

# 確認手順

- [ ] 該当unit testが通る
