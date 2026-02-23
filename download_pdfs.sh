#!/bin/bash
DIR="data/comcbt"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

download() {
  local file="$1" url="$2" ref="$3"
  if [ -f "$DIR/$file" ]; then
    echo "SKIP (exists): $file"
    return
  fi
  echo "Downloading: $file"
  curl -s -L -o "$DIR/$file" "$url" -H "Referer: $ref" -H "User-Agent: $UA"
  if [ $? -eq 0 ] && [ -s "$DIR/$file" ]; then
    echo "  OK: $(wc -c < "$DIR/$file") bytes"
  else
    echo "  FAILED: $file"
  fi
}

# 2020-08-22 (3회) - doc 4494600
download "식물보호산업기사20200822(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274866&sid=e99e85043cdf3d047990cf7c6e2724e2&module_srl=3025566" "https://www.comcbt.com/xe/eq/4494600"
download "식물보호산업기사20200822(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274870&sid=dd2bea74ed603c716267c92f8d4959ee&module_srl=3025566" "https://www.comcbt.com/xe/eq/4494600"

# 2020-06-06 (1,2회) - doc 4386501
download "식물보호산업기사20200606(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274827&sid=98014b7d26894f355f1da8216d2a1120&module_srl=3025566" "https://www.comcbt.com/xe/eq/4386501"
download "식물보호산업기사20200606(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274833&sid=51c80a3fbe895eedac788c6b34cc6351&module_srl=3025566" "https://www.comcbt.com/xe/eq/4386501"

# 2019-09-21 (4회) - doc 4059160
download "식물보호산업기사20190921(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274783&sid=cc773f919740e7400e7d09cbe7bb8539&module_srl=3025566" "https://www.comcbt.com/xe/eq/4059160"
download "식물보호산업기사20190921(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274789&sid=b257f6e8063e5534067ef1abdf5416f0&module_srl=3025566" "https://www.comcbt.com/xe/eq/4059160"

# 2019-04-27 (2회) - doc 3740487
download "식물보호산업기사20190427(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274745&sid=565b7b6eb5ab06bcb48291ac817f5c1b&module_srl=3025566" "https://www.comcbt.com/xe/eq/3740487"
download "식물보호산업기사20190427(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274751&sid=6cd7c3ef65ed7917cc15b496a06f2e59&module_srl=3025566" "https://www.comcbt.com/xe/eq/3740487"

# 2019-03-03 (1회) - doc 3740475
download "식물보호산업기사20190303(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274703&sid=5ddf3287e5c989820290a548283b13c4&module_srl=3025566" "https://www.comcbt.com/xe/eq/3740475"
download "식물보호산업기사20190303(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274709&sid=0f8bde5f7a000551251dbfc345074d8e&module_srl=3025566" "https://www.comcbt.com/xe/eq/3740475"

# 2018-09-15 (4회) - doc 3145994
download "식물보호산업기사20180915(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274653&sid=2a2a2ffcbaa60c84b94502fb7c881d99&module_srl=3025566" "https://www.comcbt.com/xe/eq/3145994"
download "식물보호산업기사20180915(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274657&sid=250885550e6c5d79f65f4e41eb69dc8b&module_srl=3025566" "https://www.comcbt.com/xe/eq/3145994"

# 2018-04-28 (2회) - doc 3055361
download "식물보호산업기사20180428(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274607&sid=f110b67f64f1432a89fa61a7197ac773&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055361"
download "식물보호산업기사20180428(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274611&sid=449bfe60d679917c9d2b8d5c62dd714a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055361"

# 2018-03-04 (1회) - doc 3055338
download "식물보호산업기사20180304(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274563&sid=d6a34da17880f51078b959287f366045&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055338"
download "식물보호산업기사20180304(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274567&sid=4cd8875b1137b8323a5b9d035a836c7a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055338"

# 2017-09-23 (4회) - doc 3055315
download "식물보호산업기사20170923(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274394&sid=3d99f3cf8705890435b381647266fdc9&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055315"
download "식물보호산업기사20170923(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274398&sid=37c6becfe2fbc0cdc64dce62a0c3d44f&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055315"

# 2017-03-05 (1회) - doc 3055242
download "식물보호산업기사20170305(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274366&sid=2b4ae94df331d0b4102511341c992cfa&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055242"
download "식물보호산업기사20170305(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274370&sid=302e74ee21df0d20ea1f6047e88570b2&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055242"

# 2016-10-01 (4회) - doc 3055218
download "식물보호산업기사20161001(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274333&sid=275124a74571ea47a51c7ebb621088ae&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055218"
download "식물보호산업기사20161001(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274337&sid=214226cc77e5db7009c1b4e5bda49882&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055218"

# 2016-03-06 (1회) - doc 3055150
download "식물보호산업기사20160306(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274298&sid=34c866498ff687c4ddce71dc7ef85611&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055150"
download "식물보호산업기사20160306(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9274300&sid=4aecdbedd7007ad24ef4796e2a78a56a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055150"

# 2015-09-19 (4회) - doc 3055126
download "식물보호산업기사20150919(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273502&sid=d35ff663bec611efa38bca4d6001ed51&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055126"
download "식물보호산업기사20150919(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273509&sid=0a1f8a784069405b3d5da71242d787e4&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055126"

# 2015-03-08 (1회) - doc 3055054
download "식물보호산업기사20150308(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273462&sid=1096dca9f92c6e703e7c362919a2e2dc&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055054"
download "식물보호산업기사20150308(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273467&sid=3f4b6b91cbe2e504cf13a784ef7686ea&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055054"

# 2014-09-20 (4회) - doc 3055028
download "식물보호산업기사20140920(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273419&sid=a019f0cbf3be0733cd982019c6885535&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055028"
download "식물보호산업기사20140920(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273428&sid=170a99d8e67141aaed6ef6761219a464&module_srl=3025566" "https://www.comcbt.com/xe/eq/3055028"

# 2013-03-10 (1회) - doc 3054852
download "식물보호산업기사20130310(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273333&sid=a784ad28344d39e066d241b53c1f4383&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054852"
download "식물보호산업기사20130310(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273337&sid=015b5a03ee25e76936fede093e778cba&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054852"

# 2012-09-15 (4회) - doc 3054830
download "식물보호산업기사20120915(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273238&sid=11a93693c094410452e2664ca4fc8546&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054830"
download "식물보호산업기사20120915(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9273240&sid=c1d17dc959e62967d3f933b6cc37b4b8&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054830"

# 2012-03-04 (1회) - doc 3054715
download "식물보호산업기사20120304(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272535&sid=21c45e8acb3045a7d792069da5355157&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054715"
download "식물보호산업기사20120304(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272540&sid=0110b03aa8b3b6128eba1c0e03366d13&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054715"

# 2011-10-02 (4회) - doc 3054674
download "식물보호산업기사20111002(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272492&sid=f0596ff64358c2b9e07f6118008b0cf4&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054674"
download "식물보호산업기사20111002(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272497&sid=ea64b594290a078ef3da65d253b4b053&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054674"

# 2011-03-20 (1회) - doc 3054519
download "식물보호산업기사20110320(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272459&sid=05024837b9c8609d89e58c77bdc45940&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054519"
download "식물보호산업기사20110320(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272462&sid=69aded805d2cc402574987cd311e730a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054519"

# 2010-09-05 (4회) - doc 3054468
download "식물보호산업기사20100905(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272428&sid=2684eeeda9c6cc3a1ee342bc331636a8&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054468"
download "식물보호산업기사20100905(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272432&sid=11c1fd95dc8b2d31623645aaa56b3d10&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054468"

# 2009-08-30 (4회) - doc 3054259
download "식물보호산업기사20090830(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272395&sid=ea7ba607039070f144424e4c1313c462&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054259"
download "식물보호산업기사20090830(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272399&sid=91b05ed127ac23823b046400f7c62fa4&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054259"

# 2008-09-07 (4회) - doc 3054042
download "식물보호산업기사20080907(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272362&sid=eb674dbcda39a16fc097467f174bf2f6&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054042"
download "식물보호산업기사20080907(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272366&sid=a9040915876db3f2caf38d416ac87e99&module_srl=3025566" "https://www.comcbt.com/xe/eq/3054042"

# 2008-03-02 (1회) - doc 3053889
download "식물보호산업기사20080302(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272311&sid=6c38c3a6b1413f3fe2e648cdbb682d48&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053889"
download "식물보호산업기사20080302(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272314&sid=1a5b717880dc93a0a381455c2b7cdba9&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053889"

# 2007-03-04 (1회) - doc 3053673
download "식물보호산업기사20070304(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272261&sid=7318f014703927835b56deb25518d10a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053673"
download "식물보호산업기사20070304(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272268&sid=cc4bef9d07e75d466ca2e9dc9d548f9a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053673"

# 2006-09-10 (4회) - doc 3053622
download "식물보호산업기사20060910(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272219&sid=f1292949d3faa6f1753743126f228b0a&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053622"
download "식물보호산업기사20060910(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272223&sid=d5e68534a645de5a8b7e5d2a44dfb8ec&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053622"

# 2006-03-05 (1회) - doc 3053469
download "식물보호산업기사20060305(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272169&sid=68f8a96057f64dfc8a09212fd0ba8cfc&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053469"
download "식물보호산업기사20060305(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272173&sid=9f9ca77fae783457265829cb5c05b280&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053469"

# 2005-09-04 (4회) - doc 3053418
download "식물보호산업기사20050904(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272140&sid=0e7287c2914680cad7899fa8e14d7dbd&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053418"
download "식물보호산업기사20050904(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272145&sid=469845e2860be68dda657e2dbd0092ad&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053418"

# 2005-03-20 (1회 추가시험) - doc 3053255
download "식물보호산업기사20050320(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272103&sid=4cf70c03cf575084dbfed4506fbc2bac&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053255"
download "식물보호산업기사20050320(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272107&sid=5640cfb09d0464b362121c4e5178467d&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053255"

# 2005-03-06 (1회) - doc 3053202
download "식물보호산업기사20050306(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272072&sid=c8c513d34121dead2baf4cba17ddc7e3&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053202"
download "식물보호산업기사20050306(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272076&sid=9ffbfee2dd42736be1c7e7f9b9f338ef&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053202"

# 2004-09-05 (4회) - doc 3053149
download "식물보호산업기사20040905(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272035&sid=5be3273bef368071caae0d7aff02ae08&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053149"
download "식물보호산업기사20040905(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272039&sid=21e25fef7ba5e66c6661a20495e659ba&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053149"

# 2004-03-07 (1회) - doc 3053005
download "식물보호산업기사20040307(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272000&sid=d2eeac4d29aa856a2a98229593763960&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053005"
download "식물보호산업기사20040307(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9272006&sid=5a2a8b0e62b442ba9da8eb5d3b6377bd&module_srl=3025566" "https://www.comcbt.com/xe/eq/3053005"

# 2003-08-31 (4회) - doc 3052958
download "식물보호산업기사20030831(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271963&sid=1ec51aad9b1051b57d7a85756e7378fc&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052958"
download "식물보호산업기사20030831(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271967&sid=bcaf275e126296b99f83970f8eae6712&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052958"

# 2003-03-16 (1회) - doc 3052795
download "식물보호산업기사20030316(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271931&sid=1ec86ce88965e2ed5eb5c32ec21506c7&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052795"
download "식물보호산업기사20030316(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271935&sid=f0d9207efb2872ceff0240339866ea22&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052795"

# 2002-09-08 (4회) - doc 3052744
download "식물보호산업기사20020908(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271892&sid=b3c6195662a2dc6d1610bb6647c0d402&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052744"
download "식물보호산업기사20020908(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271900&sid=8320496c5c676b47cba8f05c9fc56591&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052744"

# 2002-03-10 (1회) - doc 3052591
download "식물보호산업기사20020310(교사용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271810&sid=bb82f73bb206be3c14152243fe9dfead&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052591"
download "식물보호산업기사20020310(학생용).pdf" "https://www.comcbt.com/xe/?module=file&act=procFileDownload&file_srl=9271814&sid=cd621c11dba956647ca6de1f28a4a667&module_srl=3025566" "https://www.comcbt.com/xe/eq/3052591"

echo ""
echo "=== DOWNLOAD COMPLETE ==="
echo "Total PDF files:"
ls -1 "$DIR"/*.pdf 2>/dev/null | wc -l
