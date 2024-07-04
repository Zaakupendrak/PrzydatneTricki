<xsl:template name="tas-header">
    <tas-header>
      
        <!-- Dla kazdego obiektu request/header (w tym atrybuty i dzieci) -->
        <xsl:for-each select="request/header">
            
            <!-- Dla kazdego atrybutu w header -->
            <xsl:for-each select="@*">
                <xsl:if test=". != ''">               
                    <mnemonic type="{local-name(.)}"><xsl:value-of select="."></xsl:value-of></mnemonic>
                </xsl:if>
            </xsl:for-each>
            
            <!-- Dla kazdego nodea w request/header -->
            <xsl:for-each select="*[. != '']">  
                    <!-- mnemonic2, w wąsach mamy skrotowiec tego co robimy przy okazji mnemonic4 -->
                    <mnemonic2 type="{local-name(.)}"><xsl:value-of select="."></xsl:value-of></mnemonic2>
                    <!-- W mnemonic3 ustawimy atrybut type ktory przyjmie wartosc local-name z elementu, a wartosc nodea bedze pusta -->
                    <mnemonic3>
                        <xsl:attribute name="type"><xsl:value-of select="local-name(.)"></xsl:value-of></xsl:attribute>
                    </mnemonic3>

                    <mnemonic4>
                        <xsl:attribute name="type"><xsl:value-of select="local-name(.)"></xsl:value-of></xsl:attribute>
                        <!-- Ustawienie wartosci textowej dla node mnemonic4 -->
                        <xsl:value-of select="."/>
                    </mnemonic4>
                </xsl:for-each>
        </xsl:for-each>


    </tas-header>
</xsl:template>
